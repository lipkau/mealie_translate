"""Mealie API client for managing recipes."""

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Settings


class MealieClient:
    """Client for interacting with Mealie API."""

    def __init__(self, settings: Settings):
        """Initialize the Mealie client.

        Args:
            settings: Application settings containing API configuration
        """
        self.base_url = settings.mealie_base_url
        self.api_token = settings.mealie_api_token
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        return session

    def get_all_recipes(self, exclude_tag: str | None = None) -> list[dict[str, Any]]:
        """Fetch all recipes from Mealie server.

        Args:
            exclude_tag: Optional tag name to exclude recipes that already have this tag

        Returns:
            List of recipe dictionaries

        Raises:
            requests.RequestException: If API request fails
        """
        recipes = []
        page = 1
        per_page = 50

        print(f"Fetching recipes from Mealie API: {self.base_url}/api/recipes")

        while True:
            url = f"{self.base_url}/api/recipes"
            params: dict[str, Any] = {
                "page": page,
                "perPage": per_page,
                "orderBy": "name",
                "orderDirection": "asc",
            }

            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()

                data: dict[str, Any] = response.json()
                batch_recipes = data.get("items", [])

                if not batch_recipes:
                    break

                # Filter out recipes with the exclude tag if specified
                # Note: We can't filter by extras.translated here because
                # the list endpoint may not include the extras field.
                # We'll need to check this during individual processing.
                if exclude_tag:
                    # For now, we'll get all recipes and filter during processing
                    # This is a limitation of the Mealie API list endpoint
                    pass

                recipes.extend(batch_recipes)

                # Check if we've reached the end
                if len(batch_recipes) < per_page:
                    break

                page += 1

            except requests.RequestException as e:
                print(f"Error fetching recipes page {page}: {e}")
                raise

        print(f"Found {len(recipes)} recipes total")
        return recipes

    def get_recipe_details(self, recipe_slug: str) -> dict[str, Any] | None:
        """Get detailed information for a specific recipe using GET /api/recipes/{slug}.

        Args:
            recipe_slug: The recipe slug/identifier

        Returns:
            Recipe details dictionary or None if not found

        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/api/recipes/{recipe_slug}"
        print(f"Fetching recipe details: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            recipe_data: dict[str, Any] = response.json()
            print(f"Successfully fetched recipe: {recipe_data.get('name', 'Unknown')}")
            return recipe_data

        except requests.HTTPError as e:
            if hasattr(e, "response") and e.response.status_code == 404:
                print(f"Recipe not found: {recipe_slug}")
                return None
            else:
                print(f"HTTP error fetching recipe details for {recipe_slug}: {e}")
                raise
        except requests.RequestException as e:
            print(f"Error fetching recipe details for {recipe_slug}: {e}")
            raise

    def update_recipe(self, recipe_slug: str, recipe_data: dict[str, Any]) -> bool:
        """Update a recipe with new data using PUT /api/recipes/{slug}.

        Args:
            recipe_slug: The recipe slug/identifier
            recipe_data: Updated recipe data (must be complete recipe object)

        Returns:
            True if update successful, False otherwise

        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/api/recipes/{recipe_slug}"
        print(f"Updating recipe: {url}")

        try:
            # Send the complete recipe object as-is
            # Mealie expects all fields to be present during updates
            print(f"Sending update for recipe: {recipe_data.get('name', 'Unknown')}")

            response = self.session.put(
                url, json=recipe_data, timeout=60
            )  # Increased timeout for larger updates
            response.raise_for_status()
            print(f"Successfully updated recipe: {recipe_slug}")
            return True

        except requests.RequestException as e:
            print(f"Error updating recipe {recipe_slug}: {e}")
            if hasattr(e, "response") and e.response:
                try:
                    error_detail = e.response.json()
                    print(f"API error details: {error_detail}")
                except (ValueError, AttributeError):
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response text: {e.response.text[:500]}")
            raise

    def mark_recipe_as_processed(self, recipe_slug: str) -> bool:
        """Mark a recipe as processed by setting extras.translated = "true".

        Args:
            recipe_slug: The recipe slug/identifier

        Returns:
            True if marked successfully, False otherwise
        """
        try:
            # First get the current recipe
            recipe = self.get_recipe_details(recipe_slug)
            if not recipe:
                return False

            # Check if already marked as processed
            if self.is_recipe_processed(recipe):
                return True  # Already processed

            # Set the processed flag in extras
            if "extras" not in recipe:
                recipe["extras"] = {}
            recipe["extras"]["translated"] = "true"

            # Update the recipe
            return self.update_recipe(recipe_slug, recipe)

        except Exception as e:
            print(f"Error marking recipe {recipe_slug} as processed: {e}")
            return False

    def is_recipe_processed(self, recipe: dict[str, Any]) -> bool:
        """Check if a recipe has been processed (translated).

        Args:
            recipe: Recipe dictionary

        Returns:
            True if recipe has been processed, False otherwise
        """
        extras = recipe.get("extras", {})
        translated_value = extras.get("translated", "")
        # Support multiple ways of marking as processed
        return translated_value.lower() in ["true", "1"]
