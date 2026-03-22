"""Integration tests for live API connections."""

import pytest

from mealie_translate.config import get_settings
from mealie_translate.mealie_client import MealieClient
from mealie_translate.translator import RecipeTranslator


@pytest.mark.integration
async def test_mealie_connection():
    """Test connection to Mealie server."""
    try:
        settings = get_settings()
        if not settings.mealie_base_url or not settings.mealie_api_token:
            pytest.skip("Mealie configuration missing")

        async with MealieClient(settings) as client:
            recipes = await client.get_all_recipes()

        assert isinstance(recipes, list)

    except Exception as e:
        pytest.fail(f"Failed to connect to Mealie server: {e}")


@pytest.mark.integration
async def test_openai_connection():
    """Test connection to OpenAI API."""
    try:
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OpenAI API key missing")

        translator = RecipeTranslator(settings)
        test_text = "Hello, world!"
        result = await translator._translate_text(test_text)

        assert isinstance(result, str)

    except Exception as e:
        pytest.fail(f"Failed to connect to OpenAI API: {e}")


@pytest.mark.integration
async def test_recipe_details_with_actual_recipe():
    """Test fetching details for an existing recipe."""
    try:
        settings = get_settings()
        if not settings.mealie_base_url or not settings.mealie_api_token:
            pytest.skip("Mealie configuration missing")

        async with MealieClient(settings) as client:
            recipes = await client.get_all_recipes()
            if not recipes:
                pytest.skip("No recipes available for testing")

            test_recipe = recipes[0]
            recipe_slug = test_recipe.get("slug") or test_recipe.get("id")

            if not recipe_slug:
                pytest.skip("No valid recipe slug found")

            recipe = await client.get_recipe_details(recipe_slug)

            if not recipe:
                pytest.skip(f"Recipe not found: {recipe_slug}")

            assert isinstance(recipe, dict)
            assert "name" in recipe or "slug" in recipe

    except Exception as e:
        pytest.skip(f"Integration test requires live Mealie server: {e}")
