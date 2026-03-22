"""Tests for unit_converter module."""

import sys
from pathlib import Path

import pytest

project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from mealie_translate.unit_converter import (
    convert_ingredient,
    convert_ingredients,
    convert_quantity,
    is_imperial_unit,
)


class TestIsImperialUnit:
    """Tests for is_imperial_unit function."""

    @pytest.mark.parametrize(
        "unit_name",
        [
            "cup",
            "cups",
            "Cup",
            "CUPS",
            "tablespoon",
            "tbsp",
            "teaspoon",
            "tsp",
            "fluid_ounce",
            "fl_oz",
            "pint",
            "pt",
            "quart",
            "qt",
            "gallon",
            "gal",
            "pound",
            "lb",
            "lbs",
            "ounce",
            "oz",
        ],
    )
    def test_imperial_units_are_detected(self, unit_name):
        assert is_imperial_unit(unit_name) is True

    @pytest.mark.parametrize(
        "unit_name",
        [
            "ml",
            "milliliter",
            "g",
            "gram",
            "kg",
            "kilogram",
            "l",
            "liter",
            "piece",
            "pinch",
            "clove",
            "",
        ],
    )
    def test_non_imperial_units_are_not_detected(self, unit_name):
        assert is_imperial_unit(unit_name) is False


class TestConvertQuantity:
    """Tests for convert_quantity function."""

    def test_convert_cups_to_ml(self):
        quantity, unit = convert_quantity(1.0, "cup")
        assert quantity == 240
        assert unit == "ml"

    def test_convert_cups_to_ml_plural(self):
        quantity, unit = convert_quantity(2.0, "cups")
        assert quantity == 480
        assert unit == "ml"

    def test_convert_tablespoon_to_ml(self):
        quantity, unit = convert_quantity(1.0, "tbsp")
        assert quantity == 15
        assert unit == "ml"

    def test_convert_teaspoon_to_ml(self):
        quantity, unit = convert_quantity(1.0, "tsp")
        assert quantity == 5
        assert unit == "ml"

    def test_convert_fluid_ounce_to_ml(self):
        quantity, unit = convert_quantity(1.0, "fl_oz")
        assert quantity == 30
        assert unit == "ml"

    def test_convert_pint_to_ml(self):
        quantity, unit = convert_quantity(1.0, "pint")
        assert quantity == 475
        assert unit == "ml"

    def test_convert_quart_to_ml(self):
        quantity, unit = convert_quantity(1.0, "quart")
        assert quantity == 945
        assert unit == "ml"

    def test_convert_gallon_to_ml(self):
        quantity, unit = convert_quantity(1.0, "gallon")
        assert quantity == 3785
        assert unit == "ml"

    def test_convert_pound_to_g(self):
        quantity, unit = convert_quantity(1.0, "lb")
        assert quantity == 455
        assert unit == "g"

    def test_convert_ounce_to_g(self):
        quantity, unit = convert_quantity(1.0, "oz")
        assert quantity == 30
        assert unit == "g"

    def test_fractional_cups(self):
        quantity, unit = convert_quantity(0.5, "cup")
        assert quantity == 120
        assert unit == "ml"

    def test_rounding_to_nearest_5(self):
        quantity, unit = convert_quantity(0.33, "cup")
        assert quantity == 80
        assert unit == "ml"

    def test_non_imperial_unit_unchanged(self):
        quantity, unit = convert_quantity(100.0, "ml")
        assert quantity == 100.0
        assert unit == "ml"

    def test_unknown_unit_unchanged(self):
        quantity, unit = convert_quantity(2.0, "piece")
        assert quantity == 2.0
        assert unit == "piece"


class TestConvertIngredient:
    """Tests for convert_ingredient function."""

    def test_convert_structured_ingredient(self):
        ingredient = {
            "quantity": 2.0,
            "unit": {"name": "cups"},
            "food": {"name": "flour"},
            "note": "2 cups all-purpose flour",
            "display": "2 cups flour",
        }
        result = convert_ingredient(ingredient)

        assert result["quantity"] == 480
        assert result["unit"]["name"] == "ml"
        assert result["display"] == "480 ml flour"

    def test_convert_ingredient_with_lb(self):
        ingredient = {
            "quantity": 1.0,
            "unit": {"name": "lb"},
            "food": {"name": "ground beef"},
            "note": "1 lb ground beef",
            "display": "1 lb ground beef",
        }
        result = convert_ingredient(ingredient)

        assert result["quantity"] == 455
        assert result["unit"]["name"] == "g"
        assert result["display"] == "455 g ground beef"

    def test_ingredient_without_unit_unchanged(self):
        ingredient = {
            "quantity": 3.0,
            "unit": None,
            "food": {"name": "eggs"},
            "note": "3 eggs",
        }
        result = convert_ingredient(ingredient)

        assert result["quantity"] == 3.0
        assert result["unit"] is None

    def test_ingredient_with_metric_unit_unchanged(self):
        ingredient = {
            "quantity": 500.0,
            "unit": {"name": "ml"},
            "food": {"name": "water"},
            "note": "500 ml water",
        }
        result = convert_ingredient(ingredient)

        assert result["quantity"] == 500.0
        assert result["unit"]["name"] == "ml"

    def test_ingredient_without_quantity_unchanged(self):
        ingredient = {
            "quantity": None,
            "unit": {"name": "cups"},
            "food": {"name": "flour"},
            "note": "flour",
        }
        result = convert_ingredient(ingredient)

        assert result["quantity"] is None
        assert result["unit"]["name"] == "cups"

    def test_original_ingredient_not_modified(self):
        original = {
            "quantity": 1.0,
            "unit": {"name": "cup"},
            "food": {"name": "sugar"},
        }
        convert_ingredient(original)

        assert original["quantity"] == 1.0
        assert original["unit"]["name"] == "cup"

    def test_integer_display_for_whole_numbers(self):
        ingredient = {
            "quantity": 2.0,
            "unit": {"name": "cups"},
            "food": {"name": "milk"},
        }
        result = convert_ingredient(ingredient)

        assert "480 ml" in result["display"]


class TestConvertIngredients:
    """Tests for convert_ingredients function."""

    def test_convert_multiple_ingredients(self):
        ingredients = [
            {
                "quantity": 2.0,
                "unit": {"name": "cups"},
                "food": {"name": "flour"},
            },
            {
                "quantity": 1.0,
                "unit": {"name": "tsp"},
                "food": {"name": "salt"},
            },
            {
                "quantity": 3.0,
                "unit": None,
                "food": {"name": "eggs"},
            },
        ]
        results = convert_ingredients(ingredients)

        assert len(results) == 3
        assert results[0]["quantity"] == 480
        assert results[0]["unit"]["name"] == "ml"
        assert results[1]["quantity"] == 5
        assert results[1]["unit"]["name"] == "ml"
        assert results[2]["quantity"] == 3.0
        assert results[2]["unit"] is None

    def test_empty_list_returns_empty(self):
        assert convert_ingredients([]) == []


class TestConsistencyWithLLMRules:
    """Tests ensuring conversion matches LLM prompt rules exactly.

    These tests verify that the programmatic conversion produces the
    same results as the LLM prompt examples in translator.py.
    """

    @pytest.mark.parametrize(
        "input_qty,input_unit,expected_qty,expected_unit",
        [
            (1.0, "cup", 240, "ml"),
            (2.0, "cups", 480, "ml"),
            (0.5, "cup", 120, "ml"),
            (1.0, "tablespoon", 15, "ml"),
            (1.0, "pound", 455, "g"),
            (8.0, "ounces", 240, "g"),
        ],
    )
    def test_matches_llm_examples(
        self, input_qty, input_unit, expected_qty, expected_unit
    ):
        """Verify conversions match examples from UNIT_CONVERSION_RULES."""
        quantity, unit = convert_quantity(input_qty, input_unit)
        assert quantity == expected_qty
        assert unit == expected_unit
