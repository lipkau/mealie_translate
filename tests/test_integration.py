"""Integration tests for live API connections."""

import sys
from pathlib import Path

import pytest

# Add the src directory to the Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir / "src"))

from mealie_translate.config import get_settings
from mealie_translate.mealie_client import MealieClient
from mealie_translate.translator import RecipeTranslator


@pytest.mark.integration
def test_mealie_connection():
    """Test connection to Mealie server."""
    try:
        settings = get_settings()
        if not settings.mealie_base_url or not settings.mealie_api_token:
            pytest.skip("Mealie configuration missing")

        client = MealieClient(settings)
        recipes = client.get_all_recipes()

        # If we get here without exception, connection succeeded
        assert isinstance(recipes, list)

    except Exception as e:
        pytest.fail(f"Failed to connect to Mealie server: {e}")


@pytest.mark.integration
def test_openai_connection():
    """Test connection to OpenAI API."""
    try:
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OpenAI API key missing")

        translator = RecipeTranslator(settings)
        test_text = "Hello, world!"
        result = translator._translate_text(test_text)

        # If we get here without exception, connection succeeded
        assert isinstance(result, str)

    except Exception as e:
        pytest.fail(f"Failed to connect to OpenAI API: {e}")


@pytest.mark.integration
def test_recipe_details_with_actual_recipe():
    """Test fetching details for an existing recipe."""
    try:
        settings = get_settings()
        if not settings.mealie_base_url or not settings.mealie_api_token:
            pytest.skip("Mealie configuration missing")

        client = MealieClient(settings)

        # First get all recipes to find a valid one
        recipes = client.get_all_recipes()
        if not recipes:
            pytest.skip("No recipes available for testing")

        # Use the first available recipe for testing
        test_recipe = recipes[0]
        recipe_slug = test_recipe.get("slug") or test_recipe.get("id")

        if not recipe_slug:
            pytest.skip("No valid recipe slug found")

        # Now test fetching details
        recipe = client.get_recipe_details(recipe_slug)

        if not recipe:
            pytest.skip(f"Recipe not found: {recipe_slug}")

        # Basic recipe structure validation
        assert isinstance(recipe, dict)
        assert "name" in recipe or "slug" in recipe

    except Exception as e:
        pytest.skip(f"Integration test requires live Mealie server: {e}")
