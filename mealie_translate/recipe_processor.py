"""Main recipe processing logic for the Mealie Recipe Translator."""

import time
from typing import Any

from .config import Settings, get_settings
from .logger import get_logger
from .mealie_client import MealieClient
from .translator import RecipeTranslator


class RecipeProcessor:
    """Orchestrates the recipe translation process."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the recipe processor.

        Args:
            settings: Application settings (optional, will load from env if
                not provided)
        """
        self.settings = settings or get_settings()
        self.mealie_client = MealieClient(self.settings)
        self.translator = RecipeTranslator(self.settings)
        self.logger = get_logger(__name__)

    def process_all_recipes(self) -> dict[str, int]:
        """Process all recipes in the Mealie server.

        Returns:
            Dictionary with processing statistics
        """
        self.logger.info("Starting recipe translation process...")

        # Get all recipes
        self.logger.info("Fetching all recipes from Mealie server...")
        all_recipes = self.mealie_client.get_all_recipes()

        if not all_recipes:
            self.logger.warning("No recipes found!")
            return {
                "total_recipes": 0,
                "processed": 0,
                "skipped": 0,
                "failed": 0,
            }

        # Filter out already processed recipes
        unprocessed_recipes = []
        for recipe in all_recipes:
            recipe_slug = recipe.get("slug") or recipe.get("id")
            if recipe_slug:
                # Get full recipe details to check if processed
                full_recipe = self.mealie_client.get_recipe_details(recipe_slug)
                if full_recipe and not self.mealie_client.is_recipe_processed(
                    full_recipe
                ):
                    unprocessed_recipes.append(recipe)
                elif full_recipe:
                    self.logger.debug(
                        "Skipping already processed recipe: "
                        f"{full_recipe.get('name', 'Unknown')}"
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

        # Process recipes in batches
        stats = {
            "total_recipes": len(unprocessed_recipes),
            "processed": 0,
            "skipped": 0,  # This will be 0 since we're already filtering
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
                f"({len(batch)} recipes)..."
            )

            batch_stats = self._process_recipe_batch(batch)

            # Update overall stats
            for key in ["processed", "skipped", "failed"]:
                stats[key] += batch_stats[key]

            remaining = stats["total_recipes"] - stats["processed"] - stats["failed"]
            self.logger.info(
                "Batch complete. "
                f"Processed: {stats['processed']}, "
                f"Failed: {stats['failed']}, "
                f"Remaining: {remaining}"
            )

            # Add delay between batches (except for the last batch)
            if batch_num < total_batches - 1:
                time.sleep(2)

        self.logger.info(
            f"Translation complete! Processed {stats['processed']} recipes."
        )
        return stats

    def process_single_recipe(self, recipe_slug: str) -> bool:
        """Process a single recipe by slug.

        Args:
            recipe_slug: The recipe slug/identifier

        Returns:
            True if processing successful, False otherwise
        """
        self.logger.info(f"Processing single recipe: {recipe_slug}")

        try:
            # Get the recipe details
            recipe = self.mealie_client.get_recipe_details(recipe_slug)
            if not recipe:
                self.logger.error(f"Recipe not found: {recipe_slug}")
                return False

            # Check if already processed
            if self.mealie_client.is_recipe_processed(recipe):
                self.logger.info(
                    f"Recipe {recipe_slug} is already processed "
                    "(has 'translated' in extras)"
                )
                return True

            # Translate the recipe
            translated_recipe = self.translator.translate_recipe(recipe)

            # Update the recipe
            success = self.mealie_client.update_recipe(recipe_slug, translated_recipe)
            if not success:
                self.logger.error(f"Failed to update recipe: {recipe_slug}")
                return False

            # Mark as processed
            mark_success = self.mealie_client.mark_recipe_as_processed(recipe_slug)
            if not mark_success:
                self.logger.warning(
                    f"Failed to mark recipe as processed: {recipe_slug}"
                )

            self.logger.info(f"Successfully processed recipe: {recipe_slug}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing recipe {recipe_slug}: {e}")
            return False

    def _filter_unprocessed_recipes(
        self, recipes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter out recipes that have already been processed.

        Note: This method is deprecated as filtering is now done in process_all_recipes
        using the extras field instead of tags.

        Args:
            recipes: List of recipe dictionaries

        Returns:
            List of unprocessed recipe dictionaries
        """
        # This method is now deprecated - filtering is done differently
        return recipes

    def _process_recipe_batch(self, recipes: list[dict[str, Any]]) -> dict[str, int]:
        """Process a batch of recipes.

        Args:
            recipes: List of recipe dictionaries to process

        Returns:
            Dictionary with batch processing statistics
        """
        stats = {"processed": 0, "skipped": 0, "failed": 0}

        for recipe in recipes:
            recipe_slug = recipe.get("slug") or recipe.get("id")
            if not recipe_slug:
                self.logger.warning("Recipe missing slug/id, skipping")
                stats["skipped"] += 1
                continue

            try:
                # Get full recipe details
                full_recipe = self.mealie_client.get_recipe_details(recipe_slug)
                if not full_recipe:
                    self.logger.error(
                        f"Failed to fetch details for recipe: {recipe_slug}"
                    )
                    stats["failed"] += 1
                    continue

                # Check if already processed (double-check)
                if self.mealie_client.is_recipe_processed(full_recipe):
                    self.logger.debug(
                        f"Recipe {recipe_slug} already processed, skipping"
                    )
                    stats["skipped"] += 1
                    continue

                # Translate the recipe
                translated_recipe = self.translator.translate_recipe(full_recipe)

                # Update the recipe in Mealie
                success = self.mealie_client.update_recipe(
                    recipe_slug, translated_recipe
                )
                if not success:
                    self.logger.error(f"Failed to update recipe: {recipe_slug}")
                    stats["failed"] += 1
                    continue

                # Mark as processed
                mark_success = self.mealie_client.mark_recipe_as_processed(recipe_slug)
                if not mark_success:
                    self.logger.warning(
                        f"Failed to mark recipe as processed: {recipe_slug}"
                    )

                stats["processed"] += 1
                self.logger.info(
                    "Successfully processed: "
                    f"{translated_recipe.get('name', recipe_slug)}"
                )

                # Small delay between recipes
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error processing recipe {recipe_slug}: {e}")
                stats["failed"] += 1

        return stats
