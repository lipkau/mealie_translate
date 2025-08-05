"""Tests for OpenAI translator."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add the src directory to the Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir / "src"))

from mealie_translate.config import Settings
from mealie_translate.translator import RecipeTranslator


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        mealie_base_url="https://test.mealie.com",
        mealie_api_token="test_token",
        openai_api_key="test_key",
        target_language="English",
    )


@pytest.fixture
def translator(mock_settings):
    """Create a RecipeTranslator instance for testing."""
    return RecipeTranslator(mock_settings)


def test_translator_initialization(mock_settings):
    """Test RecipeTranslator initialization."""
    translator = RecipeTranslator(mock_settings)

    assert translator.target_language == "English"
    assert translator.max_retries == 3
    assert translator.retry_delay == 1.0


def test_translate_text_with_unit_conversion(translator):
    """Test text translation with imperial to metric unit conversion."""
    # Mock the _call_openai method to return a converted result
    translator._call_openai = Mock(return_value="480 ml flour")

    result = translator._translate_text("2 cups flour")

    assert result == "480 ml flour"

    # Verify the prompt includes unit conversion instructions
    call_args = translator._call_openai.call_args
    prompt = call_args[0][0]  # First argument to _call_openai
    assert "UNIT CONVERSION RULES" in prompt
    assert "cups to ml" in prompt
    assert "pounds (lbs) to g" in prompt
    assert "F or Fahrenheit to C" in prompt


def test_translate_recipe_structure(translator):
    """Test that translate_recipe maintains recipe structure."""
    original_recipe = {
        "name": "Test Recipe",
        "description": "Test description",
        "recipeInstructions": [{"text": "Step 1"}, {"text": "Step 2"}],
        "recipeIngredient": [{"note": "Ingredient 1"}, {"originalText": "1 cup flour"}],
        "notes": [{"title": "Note Title", "text": "Note text"}],
    }

    # Mock the translation methods to return test values
    translator._translate_text = Mock(side_effect=lambda x: f"Translated: {x}")
    translator._translate_instructions = Mock(
        return_value=original_recipe["recipeInstructions"]
    )
    translator._translate_ingredients = Mock(
        return_value=original_recipe["recipeIngredient"]
    )
    translator._translate_notes = Mock(return_value=original_recipe["notes"])

    result = translator.translate_recipe(original_recipe)

    # Check that all expected fields are present
    assert "name" in result
    assert "description" in result
    assert "recipeInstructions" in result
    assert "recipeIngredient" in result
    assert "notes" in result


def test_translate_instructions(translator):
    """Test instruction translation."""
    instructions = [
        {"text": "Step 1: Do something"},
        {"text": "Step 2: Do something else"},
    ]

    translator._translate_text = Mock(side_effect=lambda x: f"Translated: {x}")

    result = translator._translate_instructions(instructions)

    assert len(result) == 2
    assert result[0]["text"] == "Translated: Step 1: Do something"
    assert result[1]["text"] == "Translated: Step 2: Do something else"


def test_translate_ingredients(translator):
    """Test ingredient translation."""
    ingredients = [
        {"note": "Salt", "originalText": "1 tsp salt"},
        {"note": "Pepper", "originalText": "1/2 tsp pepper"},
    ]

    # Mock batch translation
    translator._translate_ingredient_batch = Mock(
        return_value=[
            "Translated Salt",
            "Translated 1 tsp salt",
            "Translated Pepper",
            "Translated 1/2 tsp pepper",
        ]
    )

    result = translator._translate_ingredients(ingredients)

    assert len(result) == 2
    assert result[0]["note"] == "Translated Salt"
    assert result[0]["originalText"] == "Translated 1 tsp salt"


def test_empty_recipe_translation(translator):
    """Test translation of empty recipe."""
    empty_recipe = {}

    result = translator.translate_recipe(empty_recipe)

    assert result == {}


def test_translate_notes(translator):
    """Test notes translation."""
    notes = [
        {"title": "Note Title", "text": "Note content"},
        {"title": "Another Note", "text": "More content"},
    ]

    translator._translate_text = Mock(side_effect=lambda x: f"Translated: {x}")

    result = translator._translate_notes(notes)

    assert len(result) == 2
    assert result[0]["title"] == "Translated: Note Title"
    assert result[0]["text"] == "Translated: Note content"
