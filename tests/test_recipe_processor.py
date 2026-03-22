"""Additional tests for recipe processor."""

from unittest.mock import AsyncMock, MagicMock, patch

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
        patch("mealie_translate.recipe_processor.MealieClient") as mock_client_class,
        patch(
            "mealie_translate.recipe_processor.RecipeTranslator"
        ) as mock_translator_class,
    ):
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        mock_translator = MagicMock()
        mock_translator_class.return_value = mock_translator

        proc = RecipeProcessor(mock_settings)
        proc.mealie_client = mock_client
        proc.translator = mock_translator
        return proc


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


async def test_process_single_recipe_not_found(processor):
    """Test process_single_recipe with recipe not found."""
    processor.mealie_client.get_recipe_details = AsyncMock(return_value=None)

    result = await processor.process_single_recipe("nonexistent-recipe")

    assert result is False
    processor.mealie_client.get_recipe_details.assert_called_once_with(
        "nonexistent-recipe"
    )


async def test_process_single_recipe_already_processed(processor):
    """Test process_single_recipe with already processed recipe."""
    processor.mealie_client.get_recipe_details = AsyncMock(
        return_value={
            "slug": "test-recipe",
            "name": "Test Recipe",
            "extras": {"translated": "true"},
        }
    )
    processor.mealie_client.is_recipe_processed = MagicMock(return_value=True)

    result = await processor.process_single_recipe("test-recipe")

    assert result is True


async def test_process_recipe_batch_empty(processor):
    """Test _process_recipe_batch_concurrent with empty recipe list."""
    result = await processor._process_recipe_batch_concurrent([])

    assert result["processed"] == 0
    assert result["failed"] == 0
    assert result["skipped"] == 0


async def test_process_all_recipes_empty(processor):
    """Test process_all_recipes with no recipes."""
    processor.mealie_client.get_all_recipes = AsyncMock(return_value=[])

    result = await processor.process_all_recipes()

    assert result["total_recipes"] == 0
    assert result["processed"] == 0
    assert result["skipped"] == 0
    assert result["failed"] == 0


async def test_process_single_recipe_success(processor):
    """Test successful single recipe processing."""
    recipe_data = {
        "slug": "test-recipe",
        "name": "Test Recipe",
        "description": "A test recipe",
        "extras": {},
    }
    translated_recipe = {
        "slug": "test-recipe",
        "name": "Translated Recipe",
        "description": "A translated recipe",
        "extras": {},
    }

    processor.mealie_client.get_recipe_details = AsyncMock(return_value=recipe_data)
    processor.mealie_client.is_recipe_processed = MagicMock(return_value=False)
    processor.mealie_client.update_recipe = AsyncMock(return_value=True)
    processor.translator.translate_recipe = AsyncMock(return_value=translated_recipe)

    result = await processor.process_single_recipe("test-recipe")

    assert result is True
    processor.translator.translate_recipe.assert_called_once()
    processor.mealie_client.update_recipe.assert_called_once()
