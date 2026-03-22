"""Tests for OpenAI translator."""

from unittest.mock import AsyncMock

import pytest

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


async def test_translate_text_with_unit_conversion(translator):
    """Test text translation with imperial to metric unit conversion."""
    translator._call_openai = AsyncMock(return_value="480 ml flour")

    result = await translator._translate_text("2 cups flour")

    assert result == "480 ml flour"

    call_args = translator._call_openai.call_args
    prompt = call_args[0][0]
    assert "UNIT CONVERSION RULES" in prompt
    assert "cups to ml" in prompt
    assert "pounds (lbs) to g" in prompt
    assert "F or Fahrenheit to C" in prompt


async def test_unit_conversion_consistency(translator):
    """Test that 1 cup conversions are consistent across ingredients."""
    translator._call_openai = AsyncMock(return_value="240 ml flour")

    await translator._translate_text("1 cup flour")

    call_args = translator._call_openai.call_args
    prompt = call_args[0][0]

    assert "1 cup = 240 ml for ALL ingredients" in prompt
    assert '"1 cup flour" becomes "240 ml flour"' in prompt
    assert '"1 cup sugar" becomes "240 ml sugar"' in prompt
    assert "INGREDIENT-INDEPENDENT" in prompt
    assert "1 cup = 240 ml (regardless of ingredient" in prompt


async def test_translate_recipe_structure(translator):
    """Test that translate_recipe maintains recipe structure."""
    original_recipe = {
        "name": "Test Recipe",
        "description": "Test description",
        "recipeInstructions": [{"text": "Step 1"}, {"text": "Step 2"}],
        "recipeIngredient": [
            {"note": "Ingredient 1"},
            {"originalText": "1 cup flour"},
        ],
        "notes": [{"title": "Note Title", "text": "Note text"}],
    }

    translator._translate_text = AsyncMock(side_effect=lambda x: f"Translated: {x}")
    translator._translate_instructions = AsyncMock(
        return_value=original_recipe["recipeInstructions"]
    )
    translator._translate_ingredients = AsyncMock(
        return_value=original_recipe["recipeIngredient"]
    )
    translator._translate_notes = AsyncMock(return_value=original_recipe["notes"])

    result = await translator.translate_recipe(original_recipe)

    assert "name" in result
    assert "description" in result
    assert "recipeInstructions" in result
    assert "recipeIngredient" in result
    assert "notes" in result


async def test_translate_instructions(translator):
    """Test instruction translation."""
    instructions = [
        {"text": "Step 1: Do something"},
        {"text": "Step 2: Do something else"},
    ]

    translator._translate_text = AsyncMock(side_effect=lambda x: f"Translated: {x}")

    result = await translator._translate_instructions(instructions)

    assert len(result) == 2
    assert result[0]["text"] == "Translated: Step 1: Do something"
    assert result[1]["text"] == "Translated: Step 2: Do something else"


async def test_translate_ingredients(translator):
    """Test ingredient translation."""
    ingredients = [
        {"note": "Salt", "originalText": "1 tsp salt"},
        {"note": "Pepper", "originalText": "1/2 tsp pepper"},
    ]

    translator._translate_ingredient_batch = AsyncMock(
        return_value=[
            "Translated Salt",
            "Translated 1 tsp salt",
            "Translated Pepper",
            "Translated 1/2 tsp pepper",
        ]
    )

    result = await translator._translate_ingredients(ingredients)

    assert len(result) == 2
    assert result[0]["note"] == "Translated Salt"
    assert result[0]["originalText"] == "Translated 1 tsp salt"


async def test_empty_recipe_translation(translator):
    """Test translation of empty recipe."""
    empty_recipe = {}

    result = await translator.translate_recipe(empty_recipe)

    assert result == {}


async def test_translate_notes(translator):
    """Test notes translation."""
    notes = [
        {"title": "Note Title", "text": "Note content"},
        {"title": "Another Note", "text": "More content"},
    ]

    translator._translate_text = AsyncMock(side_effect=lambda x: f"Translated: {x}")

    result = await translator._translate_notes(notes)

    assert len(result) == 2
    assert result[0]["title"] == "Translated: Note Title"
    assert result[0]["text"] == "Translated: Note content"
