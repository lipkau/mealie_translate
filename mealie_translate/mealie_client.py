"""Mealie API client for managing recipes."""

import asyncio
from typing import Any

import httpx

from .config import Settings
from .logger import get_logger


class MealieClient:
    """Async client for interacting with Mealie API."""

    def __init__(self, settings: Settings):
        """Initialize the Mealie client.

        Args:
            settings: Application settings containing API configuration
        """
        self.base_url = settings.mealie_base_url
        self.api_token = settings.mealie_api_token
        self.processed_tag = settings.processed_tag
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        self._client: httpx.AsyncClient | None = None
        self._http_version_logged = False
        self.logger = get_logger(__name__)

    async def __aenter__(self) -> "MealieClient":
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            http2=True,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(30.0, read=60.0),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising if not initialized."""
        if self._client is None:
            raise RuntimeError(
                "MealieClient must be used as async context manager: "
                "async with MealieClient(settings) as client: ..."
            )
        return self._client

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            url: Request URL
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response

        Raises:
            httpx.HTTPStatusError: If request fails after all retries
        """
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                if not self._http_version_logged:
                    self.logger.info(f"HTTP protocol: {response.http_version}")
                    self._http_version_logged = True
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 502, 503, 504]:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        self.logger.warning(
                            f"Request failed with {e.response.status_code}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                    continue
                raise
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    self.logger.warning(
                        f"Request error: {e}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                continue

        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry loop")

    async def get_all_recipes(
        self, exclude_tag: str | None = None
    ) -> list[dict[str, Any]]:
        """Fetch all recipes from Mealie server.

        Args:
            exclude_tag: Optional tag name to exclude recipes that already have this tag

        Returns:
            List of recipe dictionaries

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        recipes: list[dict[str, Any]] = []
        page = 1
        per_page = 50

        self.logger.info(
            f"Fetching recipes from Mealie API: {self.base_url}/api/recipes"
        )

        while True:
            url = f"{self.base_url}/api/recipes"
            params: dict[str, Any] = {
                "page": page,
                "perPage": per_page,
                "orderBy": "name",
                "orderDirection": "asc",
            }

            try:
                response = await self._request_with_retry("GET", url, params=params)
                data: dict[str, Any] = response.json()
                batch_recipes = data.get("items", [])

                if not batch_recipes:
                    break

                recipes.extend(batch_recipes)

                if len(batch_recipes) < per_page:
                    break

                page += 1

            except httpx.HTTPStatusError as e:
                self.logger.error(f"Error fetching recipes page {page}: {e}")
                raise

        self.logger.info(f"Found {len(recipes)} recipes total")
        return recipes

    async def get_recipe_details(self, recipe_slug: str) -> dict[str, Any] | None:
        """Get detailed information for a specific recipe.

        Args:
            recipe_slug: The recipe slug/identifier

        Returns:
            Recipe details dictionary or None if not found

        Raises:
            httpx.HTTPStatusError: If API request fails (except 404)
        """
        url = f"{self.base_url}/api/recipes/{recipe_slug}"
        self.logger.debug(f"Fetching recipe details: {url}")

        try:
            response = await self._request_with_retry("GET", url)
            recipe_data: dict[str, Any] = response.json()
            self.logger.debug(
                f"Successfully fetched recipe: {recipe_data.get('name', 'Unknown')}"
            )
            return recipe_data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Recipe not found: {recipe_slug}")
                return None
            self.logger.error(
                f"HTTP error fetching recipe details for {recipe_slug}: {e}"
            )
            raise

    async def update_recipe(
        self, recipe_slug: str, recipe_data: dict[str, Any]
    ) -> bool:
        """Update a recipe with new data.

        Args:
            recipe_slug: The recipe slug/identifier
            recipe_data: Updated recipe data (must be complete recipe object)

        Returns:
            True if update successful, False otherwise

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self.base_url}/api/recipes/{recipe_slug}"
        self.logger.debug(f"Updating recipe: {url}")

        try:
            self.logger.debug(
                f"Sending update for recipe: {recipe_data.get('name', 'Unknown')}"
            )

            await self._request_with_retry("PUT", url, json=recipe_data)
            self.logger.info(f"Successfully updated recipe: {recipe_slug}")
            return True

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Error updating recipe {recipe_slug}: {e}")
            if e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                try:
                    error_detail = e.response.json()
                    self.logger.error(f"API error details: {error_detail}")
                except (ValueError, AttributeError):
                    self.logger.error(f"Response text: {e.response.text[:500]}")
            raise

    async def mark_recipe_as_processed(self, recipe_slug: str) -> bool:
        """Mark a recipe as processed by setting the configured extras marker.

        Args:
            recipe_slug: The recipe slug/identifier

        Returns:
            True if marked successfully, False otherwise
        """
        try:
            recipe = await self.get_recipe_details(recipe_slug)
            if not recipe:
                return False

            if self.is_recipe_processed(recipe):
                return True

            self.set_recipe_processed_marker(recipe)

            return await self.update_recipe(recipe_slug, recipe)

        except Exception as e:
            self.logger.error(f"Error marking recipe {recipe_slug} as processed: {e}")
            return False

    def is_recipe_processed(self, recipe: dict[str, Any]) -> bool:
        """Check if a recipe has been processed (translated).

        Args:
            recipe: Recipe dictionary

        Returns:
            True if recipe has been processed, False otherwise
        """
        extras = recipe.get("extras", {})
        processed_value = extras.get(self.processed_tag, "")
        return str(processed_value).lower() in ["true", "1"]

    def set_recipe_processed_marker(self, recipe: dict[str, Any]) -> None:
        """Set the configured processed-marker flag on a recipe payload."""
        extras = recipe.setdefault("extras", {})
        extras[self.processed_tag] = "true"
