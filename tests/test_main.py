"""Tests for main module."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from mealie_translate.main import async_main, main


@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
def test_main_help_exit(mock_parse_args, mock_processor_class, mock_get_settings):
    """Test main function with help argument exits cleanly."""
    mock_parse_args.side_effect = SystemExit(0)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
async def test_async_main_missing_config(
    mock_parse_args, mock_processor_class, mock_get_settings
):
    """Test async_main function with missing configuration."""
    mock_args = Mock()
    mock_args.recipe = None
    mock_args.config = None
    mock_args.skip_organise = False
    mock_parse_args.return_value = mock_args

    mock_settings = Mock()
    mock_settings.mealie_base_url = None
    mock_get_settings.return_value = mock_settings

    result = await async_main()
    assert result == 1


@patch("mealie_translate.main.RecipeOrganizer")
@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
async def test_async_main_single_recipe(
    mock_parse_args, mock_processor_class, mock_get_settings, mock_organizer_class
):
    """Test async_main function with single recipe processing."""
    mock_args = Mock()
    mock_args.recipe = "test-recipe"
    mock_args.config = None
    mock_args.skip_organise = True
    mock_parse_args.return_value = mock_args

    mock_settings = Mock()
    mock_settings.mealie_base_url = "https://test.com"
    mock_settings.openai_api_key = "test-key"
    mock_settings.mealie_api_token = "test-token"
    mock_get_settings.return_value = mock_settings

    mock_processor = MagicMock()
    mock_processor.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor.__aexit__ = AsyncMock(return_value=None)
    mock_processor.process_single_recipe = AsyncMock(return_value=True)
    mock_processor_class.return_value = mock_processor

    result = await async_main()
    assert result == 0
    mock_processor.process_single_recipe.assert_called_once_with("test-recipe")


@patch("mealie_translate.main.RecipeOrganizer")
@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
async def test_async_main_all_recipes(
    mock_parse_args, mock_processor_class, mock_get_settings, mock_organizer_class
):
    """Test async_main function with all recipes processing."""
    mock_args = Mock()
    mock_args.recipe = None
    mock_args.config = None
    mock_args.skip_organise = True
    mock_parse_args.return_value = mock_args

    mock_settings = Mock()
    mock_settings.mealie_base_url = "https://test.com"
    mock_settings.openai_api_key = "test-key"
    mock_settings.mealie_api_token = "test-token"
    mock_get_settings.return_value = mock_settings

    mock_processor = MagicMock()
    mock_processor.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor.__aexit__ = AsyncMock(return_value=None)
    mock_processor.process_all_recipes = AsyncMock(
        return_value={"processed": 5, "failed": 0}
    )
    mock_processor_class.return_value = mock_processor

    result = await async_main()
    assert result == 0
    mock_processor.process_all_recipes.assert_called_once()


@patch("mealie_translate.main.get_settings")
@patch("sys.argv", ["main.py"])
async def test_async_main_exception_handling(mock_get_settings):
    """Test async_main function handles exceptions properly."""
    mock_get_settings.side_effect = Exception("Test exception")

    result = await async_main()
    assert result == 1
