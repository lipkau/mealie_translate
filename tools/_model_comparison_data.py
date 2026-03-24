"""Shared test cases and configuration for model comparison tools.

This module contains the test data used by both basic_model_comparison.py
and detailed_model_comparison.py, ensuring consistency and eliminating
duplication.
"""

from typing import TypedDict

from mealie_translate.organizer import ALLOWED_CATEGORIES


class UnitTestCase(TypedDict):
    """Unit-conversion comparison case."""

    name: str
    input: str
    expected_output: str
    key_elements: list[str]


class ComparisonRecipe(TypedDict):
    """Recipe payload used to render comparison prompts."""

    name: str
    description: str
    ingredients: str
    available_tags: str
    existing_categories: str
    existing_tags: str


class TagTestCase(TypedDict):
    """Tag-generation comparison case."""

    name: str
    recipe: ComparisonRecipe
    expected_tags: list[str]
    forbidden: list[str]


class CategoryRecipe(TypedDict):
    """Recipe payload for category-generation prompts."""

    name: str
    description: str
    ingredients: str
    existing_tags: str
    existing_categories: str


class CategoryTestCase(TypedDict):
    """Category-generation comparison case."""

    name: str
    recipe: CategoryRecipe
    expected_categories: list[str]
    must_not_include: list[str]


AVAILABLE_MODELS: list[str] = [
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-4.1-nano",
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-4o-mini",
    "gpt-4o",
]

UNIT_TEST_CASES: list[UnitTestCase] = [
    {
        "name": "Fraction: 3/4 cup",
        "input": "3/4 cup all-purpose flour",
        "expected_output": "180 ml all-purpose flour",
        "key_elements": ["180", "ml"],
    },
    {
        "name": "Fraction: 1/3 cup",
        "input": "1/3 cup honey",
        "expected_output": "80 ml honey",
        "key_elements": ["80", "ml"],
    },
    {
        "name": "Stick of butter (domain knowledge)",
        "input": "2 sticks of butter, softened",
        "expected_output": "226 g butter, softened",
        "key_elements": ["226", "g"],
    },
    {
        "name": "Mixed number: 2 1/4 cups",
        "input": "2 1/4 cups whole milk",
        "expected_output": "540 ml whole milk",
        "key_elements": ["540", "ml"],
    },
    {
        "name": "Gas Mark temperature (UK unit)",
        "input": "Preheat the oven to Gas Mark 6",
        "expected_output": "Preheat the oven to 200°C",
        "key_elements": ["200", "°C"],
    },
    {
        "name": "Passthrough — already metric",
        "input": "Bring 500 ml of water to a boil at 100°C",
        "expected_output": "Bring 500 ml of water to a boil at 100°C",
        "key_elements": ["500", "ml", "100", "°C"],
    },
    {
        "name": "Multi-unit instruction",
        "input": "Rub 2 lbs of pork with 1/4 cup spice blend and roast at 325°F for 2 hours",
        "expected_output": "Rub 910 g pork with 60 ml spice blend and roast at 165°C for 2 hours",
        "key_elements": ["910", "g", "60", "ml", "165", "°C"],
    },
]

_CATEGORY_WORD_LIST = sorted(ALLOWED_CATEGORIES)

TAG_TEST_CASES: list[TagTestCase] = [
    {
        "name": "Carbonara — cuisine + no category bleed",
        "recipe": {
            "name": "Spaghetti Carbonara",
            "description": "Classic Roman pasta dish with guanciale, eggs, pecorino and black pepper.",
            "ingredients": "spaghetti, guanciale, eggs, pecorino romano, black pepper",
            "available_tags": "",
            "existing_categories": "dinner",
            "existing_tags": "",
        },
        "expected_tags": ["italian", "pasta"],
        "forbidden": _CATEGORY_WORD_LIST,
    },
    {
        "name": "Pancakes — no 'breakfast' as a tag",
        "recipe": {
            "name": "Fluffy Buttermilk Pancakes",
            "description": "Light and fluffy pancakes made with buttermilk and vanilla, served with maple syrup.",
            "ingredients": "flour, buttermilk, eggs, butter, sugar, baking powder, vanilla extract",
            "available_tags": "",
            "existing_categories": "breakfast",
            "existing_tags": "",
        },
        "expected_tags": ["sweet"],
        "forbidden": ["breakfast", "brunch", "lunch", "dinner"],
    },
]

CATEGORY_TEST_CASES: list[CategoryTestCase] = [
    {
        "name": "Chocolate Lava Cake → dessert",
        "recipe": {
            "name": "Chocolate Lava Cake",
            "description": "Warm individual chocolate cakes with a molten center, served with vanilla ice cream.",
            "ingredients": "dark chocolate, butter, eggs, sugar, flour, vanilla",
            "existing_tags": "chocolate, baked, sweet",
            "existing_categories": "",
        },
        "expected_categories": ["dessert"],
        "must_not_include": ["dinner", "lunch", "breakfast", "main"],
    },
    {
        "name": "Hummus → condiment (no legacy 'main')",
        "recipe": {
            "name": "Classic Hummus",
            "description": "Creamy Middle Eastern chickpea dip with tahini, lemon and garlic.",
            "ingredients": "chickpeas, tahini, lemon juice, garlic cloves, olive oil, cumin, paprika",
            "existing_tags": "middle-eastern, vegetarian, no-cook",
            "existing_categories": "",
        },
        "expected_categories": ["condiment"],
        "must_not_include": ["main", "dinner"],
    },
]
