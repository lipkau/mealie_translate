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


async def test_process_single_recipe_uses_configured_processed_marker(mock_settings):
    """Test successful processing uses the configured extras marker key."""
    custom_settings = mock_settings.model_copy(update={"processed_tag": "done_flag"})

    with (
        patch("mealie_translate.recipe_processor.MealieClient") as mock_client_class,
        patch(
            "mealie_translate.recipe_processor.RecipeTranslator"
        ) as mock_translator_class,
    ):
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.is_recipe_processed = MagicMock(return_value=False)
        mock_client.get_recipe_details = AsyncMock(
            return_value={"slug": "test-recipe", "name": "Test Recipe", "extras": {}}
        )
        mock_client.update_recipe = AsyncMock(return_value=True)
        mock_client.set_recipe_processed_marker = MagicMock(
            side_effect=lambda recipe: recipe.setdefault("extras", {}).update(
                {"done_flag": "true"}
            )
        )
        mock_client_class.return_value = mock_client

        mock_translator = MagicMock()
        mock_translator.translate_recipe = AsyncMock(
            return_value={
                "slug": "test-recipe",
                "name": "Translated Recipe",
                "extras": {},
            }
        )
        mock_translator_class.return_value = mock_translator

        processor = RecipeProcessor(custom_settings)
        processor.mealie_client = mock_client
        processor.translator = mock_translator

        result = await processor.process_single_recipe("test-recipe")

        assert result is True
        mock_client.set_recipe_processed_marker.assert_called_once()
        updated_recipe = mock_client.update_recipe.await_args.args[1]
        assert updated_recipe["extras"] == {"done_flag": "true"}


# --- Dry Run Tests ---


@pytest.fixture
def dry_run_settings():
    """Create settings with dry_run enabled."""
    return Settings(
        mealie_base_url="https://test.mealie.com",
        mealie_api_token="test_token",
        openai_api_key="test_openai_key",
        target_language="English",
        dry_run=True,
    )


@pytest.fixture
def dry_run_processor(dry_run_settings):
    """Create a RecipeProcessor instance with dry_run enabled."""
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

        proc = RecipeProcessor(dry_run_settings, dry_run=True)
        proc.mealie_client = mock_client
        proc.translator = mock_translator
        return proc


async def test_dry_run_does_not_update_recipe(dry_run_processor):
    """Test that dry_run mode does not call update_recipe."""
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

    dry_run_processor.mealie_client.get_recipe_details = AsyncMock(
        return_value=recipe_data
    )
    dry_run_processor.mealie_client.is_recipe_processed = MagicMock(return_value=False)
    dry_run_processor.mealie_client.update_recipe = AsyncMock(return_value=True)
    dry_run_processor.translator.translate_recipe = AsyncMock(
        return_value=translated_recipe
    )

    result = await dry_run_processor.process_single_recipe("test-recipe")

    assert result is True
    dry_run_processor.translator.translate_recipe.assert_called_once()
    dry_run_processor.mealie_client.update_recipe.assert_not_called()


async def test_dry_run_batch_does_not_update(dry_run_processor):
    """Test that dry_run mode in batch processing does not call update_recipe."""
    recipe = {
        "slug": "test-recipe",
        "name": "Test Recipe",
        "extras": {},
    }
    translated_recipe = {
        "slug": "test-recipe",
        "name": "Translated Recipe",
        "extras": {},
    }

    dry_run_processor.mealie_client.is_recipe_processed = MagicMock(return_value=False)
    dry_run_processor.mealie_client.update_recipe = AsyncMock(return_value=True)
    dry_run_processor.translator.translate_recipe = AsyncMock(
        return_value=translated_recipe
    )

    result = await dry_run_processor._process_single_recipe_in_batch(recipe)

    assert result["status"] == "processed"
    dry_run_processor.translator.translate_recipe.assert_called_once()
    dry_run_processor.mealie_client.update_recipe.assert_not_called()


def test_dry_run_parameter_overrides_settings(mock_settings):
    """Test that dry_run parameter overrides settings."""
    with (
        patch("mealie_translate.recipe_processor.MealieClient"),
        patch("mealie_translate.recipe_processor.RecipeTranslator"),
    ):
        proc = RecipeProcessor(mock_settings, dry_run=True)
        assert proc.dry_run is True

        proc2 = RecipeProcessor(mock_settings, dry_run=False)
        assert proc2.dry_run is False


def test_dry_run_from_settings(dry_run_settings):
    """Test that dry_run is read from settings when not passed as parameter."""
    with (
        patch("mealie_translate.recipe_processor.MealieClient"),
        patch("mealie_translate.recipe_processor.RecipeTranslator"),
    ):
        proc = RecipeProcessor(dry_run_settings)
        assert proc.dry_run is True
