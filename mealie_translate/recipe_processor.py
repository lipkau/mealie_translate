"""Main recipe processing logic for the Mealie Recipe Translator."""

import asyncio
from typing import Any

from .config import Settings, get_settings
from .logger import get_logger
from .mealie_client import MealieClient
from .translator import RecipeTranslator


class RecipeProcessor:
    """Orchestrates the recipe translation process with concurrent processing."""

    def __init__(self, settings: Settings | None = None, dry_run: bool = False):
        """Initialize the recipe processor.

        Args:
            settings: Application settings (optional, will load from env if
                not provided)
            dry_run: If True, preview changes without saving to Mealie
        """
        self.settings = settings or get_settings()
        self.dry_run = dry_run or self.settings.dry_run
        self.mealie_client = MealieClient(self.settings)
        self.translator = RecipeTranslator(self.settings)
        self.logger = get_logger(__name__)
        self._mealie_semaphore = asyncio.Semaphore(
            self.settings.max_concurrent_requests
        )
        self._openai_semaphore = asyncio.Semaphore(
            self.settings.max_concurrent_translations
        )

    async def __aenter__(self) -> "RecipeProcessor":
        """Enter async context manager."""
        await self.mealie_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.mealie_client.__aexit__(exc_type, exc_val, exc_tb)

    async def process_all_recipes(self) -> dict[str, int]:
        """Process all recipes in the Mealie server with concurrent fetching.

        Returns:
            Dictionary with processing statistics
        """
        self.logger.info("Starting recipe translation process...")

        self.logger.info("Fetching all recipes from Mealie server...")
        all_recipes = await self.mealie_client.get_all_recipes()

        if not all_recipes:
            self.logger.warning("No recipes found!")
            return {
                "total_recipes": 0,
                "processed": 0,
                "skipped": 0,
                "failed": 0,
            }

        self.logger.info(
            f"Fetching details for {len(all_recipes)} recipes concurrently..."
        )
        slugs: list[str] = []
        for r in all_recipes:
            slug = r.get("slug") or r.get("id")
            if slug:
                slugs.append(slug)

        details_results = await asyncio.gather(
            *[self._fetch_with_semaphore(slug) for slug in slugs],
            return_exceptions=True,
        )

        unprocessed_recipes: list[dict[str, Any]] = []
        for result in details_results:
            if isinstance(result, BaseException):
                self.logger.error(f"Error fetching recipe details: {result}")
                continue
            if result is not None and not self.mealie_client.is_recipe_processed(
                result
            ):
                unprocessed_recipes.append(result)
            elif result is not None:
                self.logger.debug(
                    f"Skipping already processed recipe: {result.get('name', 'Unknown')}"
                )

        if not unprocessed_recipes:
            self.logger.info("No unprocessed recipes found!")
            return {
                "total_recipes": len(all_recipes),
                "processed": 0,
                "skipped": len(all_recipes),
                "failed": 0,
            }

        self.logger.info(
            f"Found {len(unprocessed_recipes)} unprocessed recipes to translate"
        )

        stats = {
            "total_recipes": len(unprocessed_recipes),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        }

        batch_size = self.settings.batch_size
        total_batches = (len(unprocessed_recipes) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = start_idx + batch_size
            batch = unprocessed_recipes[start_idx:end_idx]

            self.logger.info(
                f"Processing batch {batch_num + 1}/{total_batches} "
                f"({len(batch)} recipes) concurrently..."
            )

            batch_stats = await self._process_recipe_batch_concurrent(batch)

            for key in ["processed", "skipped", "failed"]:
                stats[key] += batch_stats[key]

            remaining = stats["total_recipes"] - stats["processed"] - stats["failed"]
            self.logger.info(
                "Batch complete. "
                f"Processed: {stats['processed']}, "
                f"Failed: {stats['failed']}, "
                f"Remaining: {remaining}"
            )

            if batch_num < total_batches - 1:
                await asyncio.sleep(1)

        self.logger.info(
            f"Translation complete! Processed {stats['processed']} recipes."
        )
        return stats

    async def process_single_recipe(self, recipe_slug: str) -> bool:
        """Process a single recipe by slug.

        Args:
            recipe_slug: The recipe slug/identifier

        Returns:
            True if processing successful, False otherwise
        """
        self.logger.info(f"Processing single recipe: {recipe_slug}")

        try:
            recipe = await self.mealie_client.get_recipe_details(recipe_slug)
            if not recipe:
                self.logger.error(f"Recipe not found: {recipe_slug}")
                return False

            if self.mealie_client.is_recipe_processed(recipe):
                self.logger.info(
                    f"Recipe {recipe_slug} is already processed "
                    "(has 'translated' in extras)"
                )
                return True

            translated_recipe = await self.translator.translate_recipe(recipe)

            if "extras" not in translated_recipe:
                translated_recipe["extras"] = {}
            translated_recipe["extras"]["translated"] = "true"

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would update recipe: {translated_recipe.get('name', recipe_slug)}"
                )
                return True

            success = await self.mealie_client.update_recipe(
                recipe_slug, translated_recipe
            )
            if not success:
                self.logger.error(f"Failed to update recipe: {recipe_slug}")
                return False

            self.logger.info(f"Successfully processed recipe: {recipe_slug}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing recipe {recipe_slug}: {e}")
            return False

    async def _fetch_with_semaphore(self, slug: str) -> dict[str, Any] | None:
        """Fetch recipe details with semaphore for rate limiting.

        Args:
            slug: Recipe slug to fetch

        Returns:
            Recipe details or None if not found
        """
        async with self._mealie_semaphore:
            return await self.mealie_client.get_recipe_details(slug)

    async def _translate_with_semaphore(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """Translate recipe with semaphore for rate limiting.

        Args:
            recipe: Recipe to translate

        Returns:
            Translated recipe
        """
        async with self._openai_semaphore:
            return await self.translator.translate_recipe(recipe)

    async def _process_single_recipe_in_batch(
        self, recipe: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a single recipe within a batch.

        Args:
            recipe: Full recipe dictionary to process

        Returns:
            Dict with status and recipe info
        """
        recipe_slug = recipe.get("slug") or recipe.get("id")
        if not recipe_slug:
            return {"status": "skipped", "reason": "missing slug/id"}

        try:
            if self.mealie_client.is_recipe_processed(recipe):
                return {"status": "skipped", "reason": "already processed"}

            translated_recipe = await self._translate_with_semaphore(recipe)

            if "extras" not in translated_recipe:
                translated_recipe["extras"] = {}
            translated_recipe["extras"]["translated"] = "true"

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would update: {translated_recipe.get('name', recipe_slug)}"
                )
                return {"status": "processed", "name": translated_recipe.get("name")}

            async with self._mealie_semaphore:
                success = await self.mealie_client.update_recipe(
                    recipe_slug, translated_recipe
                )

            if not success:
                return {"status": "failed", "reason": "update failed"}

            self.logger.info(
                f"Successfully processed: {translated_recipe.get('name', recipe_slug)}"
            )
            return {"status": "processed", "name": translated_recipe.get("name")}

        except Exception as e:
            self.logger.error(f"Error processing recipe {recipe_slug}: {e}")
            return {"status": "failed", "reason": str(e)}

    async def _process_recipe_batch_concurrent(
        self, recipes: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Process a batch of recipes concurrently.

        Args:
            recipes: List of full recipe dictionaries to process

        Returns:
            Dictionary with batch processing statistics
        """
        stats = {"processed": 0, "skipped": 0, "failed": 0}

        results = await asyncio.gather(
            *[self._process_single_recipe_in_batch(recipe) for recipe in recipes],
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, BaseException):
                self.logger.error(f"Unexpected error in batch processing: {result}")
                stats["failed"] += 1
            elif isinstance(result, dict):
                if result.get("status") == "processed":
                    stats["processed"] += 1
                elif result.get("status") == "skipped":
                    stats["skipped"] += 1
                else:
                    stats["failed"] += 1
            else:
                stats["failed"] += 1

        return stats
