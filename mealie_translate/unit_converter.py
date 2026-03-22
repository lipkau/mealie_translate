"""Unit conversion module using Pint with custom cooking unit definitions.

This module provides deterministic imperial-to-metric conversion for structured
ingredient fields, using the same conversion factors as the LLM prompts to
ensure consistency between text and structured data.
"""

from typing import Any

import pint

from .logger import get_logger

logger = get_logger(__name__)


def _create_cooking_unit_registry() -> pint.UnitRegistry:
    """Create a Pint UnitRegistry with custom cooking unit definitions.

    The conversion factors match those used in the LLM translation prompts
    to ensure consistency between text translations and structured field
    conversions.

    Returns:
        UnitRegistry configured with cooking-friendly conversion factors
    """
    ureg = pint.UnitRegistry()

    ureg.define("cooking_cup = 240 * milliliter = cup = cups = cp")
    ureg.define(
        "cooking_tablespoon = 15 * milliliter = tbsp = tablespoon = tablespoons"
    )
    ureg.define("cooking_teaspoon = 5 * milliliter = tsp = teaspoon = teaspoons")
    ureg.define(
        "cooking_fluid_ounce = 30 * milliliter = fl_oz = floz = fluid_ounce = fluid_ounces"
    )
    ureg.define("cooking_pint = 475 * milliliter = pt = pint = pints")
    ureg.define("cooking_quart = 945 * milliliter = qt = quart = quarts")
    ureg.define("cooking_gallon = 3785 * milliliter = gal = gallon = gallons")

    ureg.define("cooking_pound = 455 * gram = lb = lbs = pound = pounds")
    ureg.define("cooking_ounce = 30 * gram = oz = ounce = ounces")

    return ureg


ureg = _create_cooking_unit_registry()

IMPERIAL_VOLUME_UNITS = {
    "cup",
    "cups",
    "cp",
    "tablespoon",
    "tablespoons",
    "tbsp",
    "teaspoon",
    "teaspoons",
    "tsp",
    "fluid_ounce",
    "fluid_ounces",
    "fl_oz",
    "floz",
    "pint",
    "pints",
    "pt",
    "quart",
    "quarts",
    "qt",
    "gallon",
    "gallons",
    "gal",
}

IMPERIAL_MASS_UNITS = {
    "pound",
    "pounds",
    "lb",
    "lbs",
    "ounce",
    "ounces",
    "oz",
}

IMPERIAL_UNITS = IMPERIAL_VOLUME_UNITS | IMPERIAL_MASS_UNITS


def is_imperial_unit(unit_name: str) -> bool:
    """Check if a unit name is an imperial unit that should be converted.

    Args:
        unit_name: The unit name to check (case-insensitive)

    Returns:
        True if the unit is imperial and should be converted to metric
    """
    return unit_name.lower().strip() in IMPERIAL_UNITS


def convert_quantity(
    quantity: float, from_unit: str, round_to: int = 5
) -> tuple[float, str]:
    """Convert a quantity from imperial to metric.

    Args:
        quantity: The numeric quantity to convert
        from_unit: The imperial unit name (e.g., "cups", "oz")
        round_to: Round the result to the nearest multiple (default: 5)

    Returns:
        Tuple of (converted_quantity, metric_unit_name)
        Returns original values if conversion fails or unit is not imperial
    """
    unit_lower = from_unit.lower().strip()

    if not is_imperial_unit(unit_lower):
        return quantity, from_unit

    try:
        pint_quantity = quantity * ureg(unit_lower)

        if unit_lower in IMPERIAL_VOLUME_UNITS:
            converted = pint_quantity.to("milliliter")
            metric_unit = "ml"
        else:
            converted = pint_quantity.to("gram")
            metric_unit = "g"

        converted_value = converted.magnitude

        if round_to > 0:
            converted_value = round(converted_value / round_to) * round_to

        return float(converted_value), metric_unit

    except (pint.UndefinedUnitError, pint.DimensionalityError) as e:
        logger.warning(f"Failed to convert {quantity} {from_unit}: {e}")
        return quantity, from_unit


def convert_ingredient(ingredient: dict[str, Any]) -> dict[str, Any]:
    """Convert a single ingredient's units from imperial to metric.

    This function modifies the structured fields of an ingredient:
    - quantity: Updated with converted numeric value
    - unit: Updated with metric unit info
    - display: Regenerated with converted values
    - note: Updated if it contains the original measurement

    Args:
        ingredient: Mealie ingredient dictionary with quantity, unit, food, etc.

    Returns:
        New ingredient dictionary with converted units (original is not modified)
    """
    converted = ingredient.copy()

    unit_info = ingredient.get("unit")
    if not unit_info:
        return converted

    unit_name = (
        unit_info.get("name", "") if isinstance(unit_info, dict) else str(unit_info)
    )

    if not unit_name or not is_imperial_unit(unit_name):
        return converted

    quantity = ingredient.get("quantity")
    if quantity is None:
        return converted

    try:
        quantity_float = float(quantity)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert quantity to float: {quantity}")
        return converted

    new_quantity, new_unit = convert_quantity(quantity_float, unit_name)

    converted["quantity"] = new_quantity

    if isinstance(unit_info, dict):
        converted["unit"] = {**unit_info, "name": new_unit}
    else:
        converted["unit"] = {"name": new_unit}

    food_name = ""
    food_info = ingredient.get("food")
    if food_info and isinstance(food_info, dict):
        food_name = food_info.get("name", "")

    display_parts = []
    if new_quantity == int(new_quantity):
        display_parts.append(str(int(new_quantity)))
    else:
        display_parts.append(str(new_quantity))
    display_parts.append(new_unit)
    if food_name:
        display_parts.append(food_name)

    converted["display"] = " ".join(display_parts)

    if ingredient.get("note"):
        old_display = ingredient.get("display", "")
        if old_display and old_display in ingredient["note"]:
            converted["note"] = ingredient["note"].replace(
                old_display, converted["display"]
            )
        else:
            converted["note"] = converted["display"]

    if ingredient.get("originalText"):
        converted["originalText"] = converted["display"]

    return converted


def convert_ingredients(ingredients: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert a list of ingredients from imperial to metric units.

    Args:
        ingredients: List of Mealie ingredient dictionaries

    Returns:
        List of ingredients with converted units
    """
    return [convert_ingredient(ing) for ing in ingredients]
