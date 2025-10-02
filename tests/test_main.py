"""Tests for main module."""

from unittest.mock import Mock, patch

import pytest

from mealie_translate.main import main


@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
def test_main_help_exit(mock_parse_args, mock_processor_class, mock_get_settings):
    """Test main function with help argument exits cleanly."""
    # Simulate --help argument causing SystemExit
    mock_parse_args.side_effect = SystemExit(0)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
def test_main_missing_config(mock_parse_args, mock_processor_class, mock_get_settings):
    """Test main function with missing configuration."""
    # Mock command line arguments
    mock_args = Mock()
    mock_args.recipe = None
    mock_args.config = None
    mock_parse_args.return_value = mock_args

    # Mock settings with missing required config
    mock_settings = Mock()
    mock_settings.mealie_base_url = None
    mock_get_settings.return_value = mock_settings

    result = main()
    assert result == 1


@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
def test_main_single_recipe(mock_parse_args, mock_processor_class, mock_get_settings):
    """Test main function with single recipe processing."""
    # Mock command line arguments
    mock_args = Mock()
    mock_args.recipe = "test-recipe"
    mock_args.config = None
    mock_parse_args.return_value = mock_args

    # Mock settings with valid config
    mock_settings = Mock()
    mock_settings.mealie_base_url = "https://test.com"
    mock_settings.openai_api_key = "test-key"
    mock_settings.mealie_api_token = "test-token"
    mock_get_settings.return_value = mock_settings

    # Mock processor
    mock_processor = Mock()
    mock_processor.process_single_recipe.return_value = True
    mock_processor_class.return_value = mock_processor

    result = main()
    assert result == 0
    mock_processor.process_single_recipe.assert_called_once_with("test-recipe")


@patch("mealie_translate.main.get_settings")
@patch("mealie_translate.main.RecipeProcessor")
@patch("mealie_translate.main.argparse.ArgumentParser.parse_args")
def test_main_all_recipes(mock_parse_args, mock_processor_class, mock_get_settings):
    """Test main function with all recipes processing."""
    # Mock command line arguments
    mock_args = Mock()
    mock_args.recipe = None
    mock_args.config = None
    mock_parse_args.return_value = mock_args

    # Mock settings with valid config
    mock_settings = Mock()
    mock_settings.mealie_base_url = "https://test.com"
    mock_settings.openai_api_key = "test-key"
    mock_settings.mealie_api_token = "test-token"
    mock_get_settings.return_value = mock_settings

    # Mock processor
    mock_processor = Mock()
    mock_processor.process_all_recipes.return_value = {"processed": 5, "failed": 0}
    mock_processor_class.return_value = mock_processor

    result = main()
    assert result == 0
    mock_processor.process_all_recipes.assert_called_once()


@patch("mealie_translate.main.get_settings")
@patch("sys.argv", ["main.py"])  # Mock sys.argv to prevent parsing issues
def test_main_exception_handling(mock_get_settings):
    """Test main function handles exceptions properly."""
    # Mock settings to raise an exception
    mock_get_settings.side_effect = Exception("Test exception")

    result = main()
    assert result == 1
