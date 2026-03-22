"""Additional integration tests for end-to-end functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mealie_translate.config import Settings
from mealie_translate.mealie_client import MealieClient
from mealie_translate.recipe_processor import RecipeProcessor
from mealie_translate.translator import RecipeTranslator


@pytest.fixture
def mock_settings():
    """Create comprehensive mock settings."""
    return Settings(
        mealie_base_url="https://test.mealie.com",
        mealie_api_token="test_token",
        openai_api_key="test_openai_key",
        target_language="English",
        processed_tag="translated",
        batch_size=5,
        max_retries=2,
        retry_delay=0.1,
    )


class TestRecipeProcessorIntegration:
    """Test recipe processor with realistic scenarios."""

    async def test_full_recipe_processing_workflow(self, mock_settings):
        """Test complete recipe processing workflow."""
        with (
            patch(
                "mealie_translate.recipe_processor.MealieClient"
            ) as mock_client_class,
            patch(
                "mealie_translate.recipe_processor.RecipeTranslator"
            ) as mock_translator_class,
        ):
            mock_client = MagicMock()
            mock_translator = MagicMock()
            mock_client_class.return_value = mock_client
            mock_translator_class.return_value = mock_translator

            sample_recipe = {
                "slug": "test-recipe",
                "name": "Test Recipe",
                "description": "A test recipe",
                "recipeIngredient": [{"note": "1 cup flour"}],
                "recipeInstructions": [{"text": "Mix ingredients"}],
                "extras": {},
            }

            translated_recipe = {
                "slug": "test-recipe",
                "name": "Test Recipe (Translated)",
                "description": "A test recipe (translated)",
                "recipeIngredient": [{"note": "240 ml flour"}],
                "recipeInstructions": [{"text": "Mix ingredients (translated)"}],
                "extras": {"translated": "true"},
            }

            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_all_recipes = AsyncMock(return_value=[sample_recipe])
            mock_client.get_recipe_details = AsyncMock(return_value=sample_recipe)
            mock_client.is_recipe_processed = MagicMock(return_value=False)
            mock_client.update_recipe = AsyncMock(return_value=True)
            mock_translator.translate_recipe = AsyncMock(return_value=translated_recipe)

            processor = RecipeProcessor(mock_settings)
            processor.mealie_client = mock_client
            processor.translator = mock_translator

            stats = await processor.process_all_recipes()

            assert stats["total_recipes"] == 1
            assert stats["processed"] == 1
            assert stats["failed"] == 0

    async def test_process_all_recipes_empty(self, mock_settings):
        """Test processing when no recipes exist."""
        with (
            patch(
                "mealie_translate.recipe_processor.MealieClient"
            ) as mock_client_class,
            patch(
                "mealie_translate.recipe_processor.RecipeTranslator"
            ) as mock_translator_class,
        ):
            mock_client = MagicMock()
            mock_translator = MagicMock()
            mock_client_class.return_value = mock_client
            mock_translator_class.return_value = mock_translator

            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_all_recipes = AsyncMock(return_value=[])

            processor = RecipeProcessor(mock_settings)
            processor.mealie_client = mock_client
            processor.translator = mock_translator

            stats = await processor.process_all_recipes()

            assert stats["total_recipes"] == 0
            assert stats["processed"] == 0
            assert stats["failed"] == 0


class TestTranslatorEdgeCases:
    """Test translator with edge cases and error conditions."""

    async def test_empty_recipe_fields(self, mock_settings):
        """Test translator handles empty or missing recipe fields."""
        translator = RecipeTranslator(mock_settings)

        translator._call_openai = AsyncMock(return_value="Translated text")

        empty_recipe = {
            "name": "",
            "description": None,
            "recipeIngredient": [],
            "recipeInstructions": [],
            "notes": [],
        }

        result = await translator.translate_recipe(empty_recipe)

        assert isinstance(result, dict)
        assert "name" in result
        assert "recipeIngredient" in result
        assert "recipeInstructions" in result

    async def test_translation_with_special_characters(self, mock_settings):
        """Test translator handles special characters and unicode."""
        translator = RecipeTranslator(mock_settings)
        translator._call_openai = AsyncMock(return_value="Translated: café")

        text_with_unicode = "café ñoño 中文 🍰"
        result = await translator._translate_text(text_with_unicode)

        assert result == "Translated: café"
        translator._call_openai.assert_called_once()


class TestMealieClientEdgeCases:
    """Test Mealie client with edge cases."""

    def test_recipe_processed_check_variations(self, mock_settings):
        """Test different ways a recipe can be marked as processed."""
        client = MealieClient(mock_settings)

        test_cases = [
            ({"extras": {"translated": "true"}}, True),
            ({"extras": {"translated": "True"}}, True),
            ({"extras": {"translated": "1"}}, True),
            ({"extras": {"translated": "false"}}, False),
            ({"extras": {"other_field": "value"}}, False),
            ({"extras": {}}, False),
            ({}, False),
        ]

        for recipe, expected in test_cases:
            result = client.is_recipe_processed(recipe)
            assert result == expected, f"Failed for recipe: {recipe}"


@pytest.mark.integration
class TestRealAPICompatibility:
    """Test compatibility with real API structures (without making actual calls)."""

    async def test_realistic_recipe_structure(self, mock_settings):
        """Test with a realistic recipe structure from Mealie."""
        realistic_recipe = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "userId": "456e7890-e89b-12d3-a456-426614174001",
            "householdId": "789e0123-e89b-12d3-a456-426614174002",
            "groupId": "012e3456-e89b-12d3-a456-426614174003",
            "name": "Chocolate Chip Cookies",
            "slug": "chocolate-chip-cookies",
            "image": "image.jpg",
            "recipeServings": 24,
            "recipeYieldQuantity": 2.0,
            "recipeYield": "2 dozen",
            "totalTime": "PT45M",
            "prepTime": "PT15M",
            "cookTime": "PT10M",
            "performTime": None,
            "description": "Classic chocolate chip cookies",
            "recipeCategory": [{"id": "cat1", "name": "Desserts"}],
            "tags": [{"id": "tag1", "name": "Baking"}],
            "tools": [{"id": "tool1", "name": "Oven"}],
            "rating": 5,
            "orgURL": "https://example.com/recipe",
            "dateAdded": "2024-01-01T12:00:00Z",
            "dateUpdated": "2024-01-02T12:00:00Z",
            "createdAt": "2024-01-01T12:00:00Z",
            "updatedAt": "2024-01-02T12:00:00Z",
            "lastMade": None,
            "recipeIngredient": [
                {
                    "quantity": 2.0,
                    "unit": {"name": "cups"},
                    "food": {"name": "flour"},
                    "note": "2 cups all-purpose flour",
                    "isFood": True,
                    "disableAmount": False,
                    "display": "2 cups all-purpose flour",
                }
            ],
            "recipeInstructions": [
                {
                    "id": "inst1",
                    "title": "Mix dry ingredients",
                    "summary": "",
                    "text": "In a bowl, mix flour and baking soda.",
                    "ingredientReferences": [],
                }
            ],
            "nutrition": {
                "calories": "150",
                "protein": "2g",
                "carbohydrates": "20g",
            },
            "settings": {
                "public": True,
                "showNutrition": True,
                "showAssets": True,
                "landscapeView": False,
                "disableComments": False,
                "disableAmount": False,
                "locked": False,
            },
            "assets": [],
            "notes": [
                {
                    "id": "note1",
                    "title": "Storage",
                    "text": "Store in airtight container for up to 1 week",
                }
            ],
            "extras": {},
            "comments": [],
        }

        translator = RecipeTranslator(mock_settings)
        translator._call_openai = AsyncMock(return_value="Translated content")

        result = await translator.translate_recipe(realistic_recipe)

        assert isinstance(result, dict)
        assert "name" in result
        assert "recipeIngredient" in result
        assert "recipeInstructions" in result
        assert "notes" in result
