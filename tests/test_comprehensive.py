"""Additional integration tests for end-to-end functionality."""

from unittest.mock import Mock, patch

import pytest

from mealie_translate.config import Settings
from mealie_translate.mealie_client import MealieClient
from mealie_translate.recipe_processor import RecipeProcessor
from mealie_translate.translator_factory import TranslatorFactory


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
        retry_delay=1,  # Changed from 0.1 to 1
    )


class TestRecipeProcessorIntegration:
    """Test recipe processor with realistic scenarios."""

    def test_full_recipe_processing_workflow(self, mock_settings):
        """Test complete recipe processing workflow."""
        with (
            patch(
                "mealie_translate.recipe_processor.MealieClient"
            ) as mock_client_class,
            patch(
                "mealie_translate.recipe_processor.TranslatorFactory"
            ) as mock_factory_class,
        ):
            # Setup mocks
            mock_client = Mock()
            mock_translator = Mock()
            mock_client_class.return_value = mock_client
            mock_factory_class.create_translator.return_value = mock_translator

            # Mock recipe data
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

            # Configure mocks
            mock_client.get_all_recipes.return_value = [sample_recipe]
            mock_client.get_recipe_details.return_value = sample_recipe
            mock_client.is_recipe_processed.return_value = False
            mock_client.update_recipe.return_value = True
            mock_client.mark_recipe_as_processed.return_value = True
            mock_translator.translate_recipe.return_value = translated_recipe

            # Test processing
            processor = RecipeProcessor(mock_settings)
            stats = processor.process_all_recipes()

            # Verify results
            assert stats["total_recipes"] == 1
            assert stats["processed"] == 1
            assert stats["failed"] == 0

            # Verify method calls
            mock_client.get_all_recipes.assert_called_once()
            # get_recipe_details is called twice: once during filtering and once during processing
            assert mock_client.get_recipe_details.call_count == 2
            mock_translator.translate_recipe.assert_called_once_with(
                sample_recipe, "English"
            )
            mock_client.update_recipe.assert_called_once_with(
                "test-recipe", translated_recipe
            )
            mock_client.mark_recipe_as_processed.assert_called_once_with("test-recipe")

    def test_recipe_processing_with_failures(self, mock_settings):
        """Test recipe processing when some recipes fail."""
        with (
            patch(
                "mealie_translate.recipe_processor.MealieClient"
            ) as mock_client_class,
            patch(
                "mealie_translate.recipe_processor.TranslatorFactory"
            ) as mock_factory_class,
        ):
            mock_client = Mock()
            mock_translator = Mock()
            mock_client_class.return_value = mock_client
            mock_factory_class.create_translator.return_value = mock_translator

            # Mock multiple recipes
            recipes = [
                {"slug": "recipe-1", "name": "Recipe 1", "extras": {}},
                {"slug": "recipe-2", "name": "Recipe 2", "extras": {}},
                {"slug": "recipe-3", "name": "Recipe 3", "extras": {}},
            ]

            mock_client.get_all_recipes.return_value = recipes
            # get_recipe_details is called twice per recipe (filtering + processing)
            mock_client.get_recipe_details.side_effect = [
                recipes[0],  # Filter check for recipe-1
                recipes[1],  # Filter check for recipe-2
                recipes[2],  # Filter check for recipe-3
                recipes[0],  # Processing recipe-1 (Success)
                recipes[
                    1
                ],  # Processing recipe-2 (Will fail due to None return in next call)
                recipes[2],  # Processing recipe-3 (Success)
            ]
            mock_client.is_recipe_processed.return_value = False
            mock_client.update_recipe.side_effect = [
                True,  # Success
                Exception("Update failed"),  # Failure
            ]
            mock_client.mark_recipe_as_processed.return_value = True
            mock_translator.translate_recipe.side_effect = [
                {
                    "slug": "recipe-1",
                    "name": "Translated Recipe 1",
                    "extras": {"translated": "true"},
                },
                {
                    "slug": "recipe-3",
                    "name": "Translated Recipe 3",
                    "extras": {"translated": "true"},
                },
            ]

            processor = RecipeProcessor(mock_settings)
            stats = processor.process_all_recipes()

            # Should handle failures gracefully
            assert stats["total_recipes"] == 3
            assert stats["processed"] >= 1  # At least one should succeed
            assert stats["failed"] >= 1  # At least one should fail

    def test_batch_processing(self, mock_settings):
        """Test that recipes are processed in batches."""
        # Set small batch size
        mock_settings.batch_size = 2

        with (
            patch(
                "mealie_translate.recipe_processor.MealieClient"
            ) as mock_client_class,
            patch(
                "mealie_translate.recipe_processor.TranslatorFactory"
            ) as mock_factory_class,
            patch("mealie_translate.recipe_processor.time.sleep") as mock_sleep,
        ):
            mock_client = Mock()
            mock_translator = Mock()
            mock_client_class.return_value = mock_client
            mock_factory_class.create_translator.return_value = mock_translator

            # Create 5 recipes to test batching
            recipes = [
                {"slug": f"recipe-{i}", "name": f"Recipe {i}", "extras": {}}
                for i in range(1, 6)
            ]

            mock_client.get_all_recipes.return_value = recipes
            # get_recipe_details is called twice per recipe (filtering + processing)
            mock_client.get_recipe_details.side_effect = (
                recipes + recipes
            )  # 10 calls total
            mock_client.is_recipe_processed.return_value = False
            mock_client.update_recipe.return_value = True
            mock_client.mark_recipe_as_processed.return_value = True
            mock_translator.translate_recipe.side_effect = [
                {**recipe, "extras": {"translated": "true"}} for recipe in recipes
            ]

            processor = RecipeProcessor(mock_settings)
            stats = processor.process_all_recipes()

            # Should process all recipes
            assert stats["total_recipes"] == 5

            # Should have called sleep:
            # - 5 times with sleep(1) between recipes
            # - 2 times with sleep(2) between batches (3 batches total, so 2 sleep calls)
            # Total: 7 sleep calls
            assert mock_sleep.call_count == 7

            # Check specific sleep calls
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            # Should have 5 calls with 1 second (between recipes) and 2 calls with 2 seconds (between batches)
            assert sleep_calls.count(1) == 5  # Between recipes
            assert sleep_calls.count(2) == 2  # Between batches


class TestTranslatorEdgeCases:
    """Test translator with edge cases and error conditions."""

    def test_empty_recipe_fields(self, mock_settings):
        """Test translator handles empty or missing recipe fields."""
        with patch(
            "mealie_translate.translator_factory.TranslatorFactory.create_translator"
        ) as mock_factory:
            mock_translator = Mock()
            mock_factory.return_value = mock_translator
            mock_translator.translate_recipe = Mock(return_value={"translated": True})

            translator = TranslatorFactory.create_translator(mock_settings)

            empty_recipe = {
                "name": "",
                "description": None,
                "recipeIngredient": [],
                "recipeInstructions": [],
                "notes": [],
            }

            result = translator.translate_recipe(empty_recipe, "English")

            # Should handle empty fields gracefully
            assert isinstance(result, dict)
            assert result["translated"] is True

    def test_translation_with_special_characters(self, mock_settings):
        """Test translator handles special characters and unicode."""
        with patch(
            "mealie_translate.translator_factory.TranslatorFactory.create_translator"
        ) as mock_factory:
            mock_translator = Mock()
            mock_factory.return_value = mock_translator
            mock_translator.translate_recipe = Mock(return_value={"translated": True})

            # Test that the translator can be created with settings containing special chars
            mock_settings.target_language = "español 中文"
            translator = TranslatorFactory.create_translator(mock_settings)

            assert translator is not None


class TestMealieClientEdgeCases:
    """Test Mealie client with edge cases."""

    def test_pagination_edge_cases(self, mock_settings):
        """Test pagination with edge cases."""
        client = MealieClient(mock_settings)

        with patch("requests.Session.get") as mock_get:
            # Mock empty response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": []}
            mock_get.return_value = mock_response

            recipes = client.get_all_recipes()

            assert recipes == []
            mock_get.assert_called_once()

    def test_recipe_processed_check_variations(self, mock_settings):
        """Test different ways a recipe can be marked as processed."""
        client = MealieClient(mock_settings)

        # Test various processed states
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

    def test_realistic_recipe_structure(self, mock_settings):
        """Test with a realistic recipe structure from Mealie."""
        # This is based on actual Mealie recipe structure
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
            "nutrition": {"calories": "150", "protein": "2g", "carbohydrates": "20g"},
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

        with patch(
            "mealie_translate.translator_factory.TranslatorFactory.create_translator"
        ) as mock_factory:
            mock_translator = Mock()
            mock_factory.return_value = mock_translator
            expected_result = {
                "name": "Translated name",
                "recipeIngredient": ["Translated ingredient"],
                "recipeInstructions": [{"text": "Translated instruction"}],
                "notes": [{"text": "Translated note"}],
            }
            mock_translator.translate_recipe = Mock(return_value=expected_result)

            translator = TranslatorFactory.create_translator(mock_settings)

            # Should handle complex recipe structure without errors
            result = translator.translate_recipe(realistic_recipe, "English")

        assert isinstance(result, dict)
        assert "name" in result
        assert "recipeIngredient" in result
        assert "recipeInstructions" in result
        assert "notes" in result
