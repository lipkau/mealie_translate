"""Tests for dry run functionality."""

from unittest.mock import Mock, patch

from mealie_translate.config import Settings
from mealie_translate.diff_utils import DiffFormatter, has_changes, log_dry_run_diff
from mealie_translate.recipe_processor import RecipeProcessor


class TestDiffFormatter:
    """Test the diff formatting functionality."""

    def test_format_recipe_diff_no_changes(self):
        """Test formatting when there are no changes."""
        original = {
            "name": "Test Recipe",
            "description": "A test recipe",
            "recipe_instructions": [{"text": "Step 1"}],
            "recipe_ingredient": [{"display": "1 cup flour"}],
        }

        # Same as original
        translated = original.copy()

        result = DiffFormatter.format_recipe_diff("Test Recipe", original, translated)
        assert "[DRY RUN] Recipe: Test Recipe" in result
        # Should have no diff boxes since no changes
        assert "┌─" not in result

    def test_format_recipe_diff_with_title_change(self):
        """Test formatting when title changes."""
        original = {
            "name": "Test Recipe",
            "description": "A test recipe",
        }

        translated = {
            "name": "Test Recipe (English)",
            "description": "A test recipe",
        }

        result = DiffFormatter.format_recipe_diff("Test Recipe", original, translated)

        assert "[DRY RUN] Recipe: Test Recipe" in result
        assert "┌─ Title" in result
        assert "- Test Recipe" in result
        assert "+ Test Recipe (English)" in result

    def test_format_recipe_diff_with_instructions_change(self):
        """Test formatting when instructions change."""
        original = {
            "name": "Test Recipe",
            "recipe_instructions": [{"text": "Preheat oven to 350°F"}],
        }

        translated = {
            "name": "Test Recipe",
            "recipe_instructions": [{"text": "Preheat oven to 175°C"}],
        }

        result = DiffFormatter.format_recipe_diff("Test Recipe", original, translated)

        assert "┌─ Instructions" in result
        assert "350°F" in result
        assert "175°C" in result

    def test_has_changes_detects_differences(self):
        """Test that has_changes correctly identifies changes."""
        original = {"name": "Original", "description": "Desc"}
        changed = {"name": "Changed", "description": "Desc"}
        same = {"name": "Original", "description": "Desc"}

        assert has_changes(original, changed) is True
        assert has_changes(original, same) is False

    def test_has_changes_with_missing_fields(self):
        """Test has_changes with missing fields."""
        original = {"name": "Test"}
        translated = {"name": "Test", "description": "New desc"}

        # Should detect the new description as a change
        assert has_changes(original, translated) is True


class TestDryRunMode:
    """Test dry run mode functionality in RecipeProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dry_run_settings = Settings(
            mealie_base_url="http://test.com",
            mealie_api_token="test-token",
            openai_api_key="test-key",
            dry_run=True,
            dry_run_limit=3,
        )

    @patch("mealie_translate.recipe_processor.logger")
    def test_dry_run_logs_diffs(self, mock_logger):
        """Test that dry run mode logs diffs instead of updating."""
        processor = RecipeProcessor(self.dry_run_settings)

        # Mock the clients
        processor.mealie_client = Mock()
        processor.translator = Mock()

        # Mock recipe data
        original_recipe = {
            "name": "Test Recipe",
            "description": "Original description",
            "recipe_instructions": [{"text": "Original step"}],
        }

        translated_recipe = {
            "name": "Test Recipe (English)",
            "description": "Translated description",
            "recipe_instructions": [{"text": "Translated step"}],
        }

        processor.mealie_client.get_recipe_details.return_value = original_recipe
        processor.mealie_client.is_recipe_processed.return_value = False
        processor.translator.translate_recipe.return_value = translated_recipe

        # Process single recipe in dry run mode
        result = processor.process_single_recipe("test-recipe")

        # Should return True (success)
        assert result is True

        # Should NOT call update methods
        processor.mealie_client.update_recipe.assert_not_called()
        processor.mealie_client.mark_recipe_as_processed.assert_not_called()

        # Should call the translator
        processor.translator.translate_recipe.assert_called_once_with(original_recipe)

    def test_dry_run_limits_recipes(self):
        """Test that dry run mode respects the limit setting."""
        processor = RecipeProcessor(self.dry_run_settings)

        # Mock the clients
        processor.mealie_client = Mock()
        processor.translator = Mock()

        # Mock 5 recipes but limit is 3
        recipes = [{"slug": f"recipe-{i}", "name": f"Recipe {i}"} for i in range(5)]

        processor.mealie_client.get_all_recipes.return_value = recipes

        # Mock recipe details - all unprocessed
        def mock_get_details(slug):
            return {"slug": slug, "name": f"Recipe for {slug}"}

        def mock_is_processed(recipe):
            return False

        processor.mealie_client.get_recipe_details.side_effect = mock_get_details
        processor.mealie_client.is_recipe_processed.side_effect = mock_is_processed

        # Mock translator to return same recipe (no changes)
        processor.translator.translate_recipe.side_effect = lambda x: x

        # Process all recipes
        with patch("builtins.print"):  # Suppress print output
            stats = processor.process_all_recipes()

        # Should only process 3 recipes due to dry_run_limit
        assert stats["processed"] == 3
        assert stats["total_recipes"] == 3  # Total should be limited too

    def test_normal_mode_updates_recipes(self):
        """Test that normal mode (not dry run) updates recipes."""
        normal_settings = Settings(
            mealie_base_url="http://test.com",
            mealie_api_token="test-token",
            openai_api_key="test-key",
            dry_run=False,  # Normal mode
        )

        processor = RecipeProcessor(normal_settings)

        # Mock the clients
        processor.mealie_client = Mock()
        processor.translator = Mock()

        original_recipe = {"name": "Test Recipe", "slug": "test-recipe"}
        translated_recipe = {"name": "Test Recipe (English)", "slug": "test-recipe"}

        processor.mealie_client.get_recipe_details.return_value = original_recipe
        processor.mealie_client.is_recipe_processed.return_value = False
        processor.mealie_client.update_recipe.return_value = True
        processor.mealie_client.mark_recipe_as_processed.return_value = True
        processor.translator.translate_recipe.return_value = translated_recipe

        # Process single recipe in normal mode
        with patch("builtins.print"):  # Suppress print output
            result = processor.process_single_recipe("test-recipe")

        # Should return True (success)
        assert result is True

        # Should call update methods in normal mode
        processor.mealie_client.update_recipe.assert_called_once_with(
            "test-recipe", translated_recipe
        )
        processor.mealie_client.mark_recipe_as_processed.assert_called_once_with(
            "test-recipe"
        )


class TestLogDryRunDiff:
    """Test the log_dry_run_diff function."""

    @patch("mealie_translate.diff_utils.logger")
    def test_log_dry_run_diff_calls_logger(self, mock_logger):
        """Test that log_dry_run_diff writes to logger."""
        original = {"name": "Original Recipe"}
        translated = {"name": "Translated Recipe"}

        log_dry_run_diff("Test Recipe", original, translated)

        # Should have made multiple logger.info calls
        assert mock_logger.info.call_count > 0

        # First call should contain the recipe name
        first_call_args = mock_logger.info.call_args_list[0][0]
        assert "Test Recipe" in first_call_args[0]
