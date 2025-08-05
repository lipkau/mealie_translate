"""Additional tests for recipe processor."""

from unittest.mock import patch

import pytest

from mealie_translate.config import Settings
from mealie_translate.recipe_processor import RecipeProcessor


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        mealie_base_url="https://test.mealie.com",
        mealie_api_token="test_token",
        openai_api_key="test_openai_key",
        target_language="English",
        processed_tag="translated",
        batch_size=5,
    )


@pytest.fixture
def processor(mock_settings):
    """Create a RecipeProcessor instance for testing."""
    with (
        patch("mealie_translate.recipe_processor.MealieClient") as _mock_client,
        patch("mealie_translate.recipe_processor.RecipeTranslator") as _mock_translator,
    ):
        return RecipeProcessor(mock_settings)


def test_processor_initialization(mock_settings):
    """Test RecipeProcessor initialization."""
    with (
        patch("mealie_translate.recipe_processor.MealieClient") as mock_client,
        patch("mealie_translate.recipe_processor.RecipeTranslator") as mock_translator,
    ):
        processor = RecipeProcessor(mock_settings)

        assert processor.settings == mock_settings
        mock_client.assert_called_once_with(mock_settings)
        mock_translator.assert_called_once_with(mock_settings)


def test_filter_unprocessed_recipes(processor):
    """Test _filter_unprocessed_recipes method (deprecated - now returns all recipes)."""
    recipes = [
        {"slug": "recipe1", "tags": []},
        {"slug": "recipe2", "tags": [{"name": "translated"}]},
        {"slug": "recipe3", "tags": [{"name": "breakfast"}]},
        {"slug": "recipe4", "tags": [{"name": "healthy"}, {"name": "translated"}]},
    ]

    unprocessed = processor._filter_unprocessed_recipes(recipes)

    # This method is now deprecated and just returns all recipes
    # Filtering is done at a higher level using the extras field
    assert len(unprocessed) == 4
    assert unprocessed == recipes


def test_process_single_recipe_not_found(processor):
    """Test process_single_recipe with recipe not found."""
    processor.mealie_client.get_recipe_details.return_value = None

    result = processor.process_single_recipe("nonexistent-recipe")

    assert result is False
    processor.mealie_client.get_recipe_details.assert_called_once_with(
        "nonexistent-recipe"
    )


def test_process_single_recipe_already_processed(processor):
    """Test process_single_recipe with already processed recipe."""
    processor.mealie_client.get_recipe_details.return_value = {
        "slug": "test-recipe",
        "name": "Test Recipe",
        "tags": [{"name": "translated"}],
    }
    processor.mealie_client.has_tag.return_value = True

    result = processor.process_single_recipe("test-recipe")

    # Returns True because the recipe is considered "successfully processed" (no work needed)
    assert result is True


@patch("mealie_translate.recipe_processor.time.sleep")
def test_process_recipe_batch_empty(mock_sleep, processor):
    """Test _process_recipe_batch with empty recipe list."""
    result = processor._process_recipe_batch([])

    assert result["processed"] == 0
    assert result["failed"] == 0
    assert mock_sleep.call_count == 0


def test_process_all_recipes_empty(processor):
    """Test process_all_recipes with no recipes."""
    processor.mealie_client.get_all_recipes.return_value = []

    result = processor.process_all_recipes()

    assert result["total_recipes"] == 0
    assert result["processed"] == 0
    assert result["skipped"] == 0
    assert result["failed"] == 0
