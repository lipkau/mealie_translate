"""Tests for Mealie API client."""

import json
import sys
from pathlib import Path

import pytest
import responses

# Add the src directory to the Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir / "src"))

from mealie_translate.config import Settings
from mealie_translate.mealie_client import MealieClient


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        mealie_base_url="https://test.mealie.com",
        mealie_api_token="test_token",
        openai_api_key="test_key",
    )


@pytest.fixture
def mealie_client(mock_settings):
    """Create a MealieClient instance for testing."""
    return MealieClient(mock_settings)


def test_mealie_client_initialization(mock_settings):
    """Test MealieClient initialization."""
    client = MealieClient(mock_settings)

    assert client.base_url == "https://test.mealie.com"
    assert client.api_token == "test_token"
    assert client.session is not None
    auth_header = client.session.headers["Authorization"]
    assert auth_header == "Bearer test_token"


@responses.activate
def test_get_recipe_details_success(mealie_client):
    """Test successful recipe details retrieval."""
    recipe_slug = "test-recipe"
    mock_recipe = {
        "slug": recipe_slug,
        "name": "Test Recipe",
        "description": "A test recipe",
        "tags": [{"name": "test"}],
    }

    responses.add(
        responses.GET,
        f"https://test.mealie.com/api/recipes/{recipe_slug}",
        json=mock_recipe,
        status=200,
    )

    recipe = mealie_client.get_recipe_details(recipe_slug)

    assert recipe == mock_recipe
    assert recipe["name"] == "Test Recipe"


@responses.activate
def test_get_recipe_details_not_found(mealie_client):
    """Test recipe details retrieval when recipe not found."""
    recipe_slug = "nonexistent-recipe"

    responses.add(
        responses.GET, f"https://test.mealie.com/api/recipes/{recipe_slug}", status=404
    )

    result = mealie_client.get_recipe_details(recipe_slug)
    assert result is None


@responses.activate
def test_update_recipe_success(mealie_client):
    """Test successful recipe update."""
    recipe_slug = "test-recipe"
    recipe_data = {"name": "Updated Recipe", "description": "Updated description"}

    responses.add(
        responses.PUT, f"https://test.mealie.com/api/recipes/{recipe_slug}", status=200
    )

    result = mealie_client.update_recipe(recipe_slug, recipe_data)

    assert result is True


def test_is_recipe_processed(mealie_client):
    """Test recipe processed status checking functionality."""
    recipe_processed = {"extras": {"translated": "true"}}
    recipe_not_processed = {"extras": {"some_other_field": "value"}}
    recipe_no_extras = {}

    assert mealie_client.is_recipe_processed(recipe_processed) is True
    assert mealie_client.is_recipe_processed(recipe_not_processed) is False
    assert mealie_client.is_recipe_processed(recipe_no_extras) is False


@responses.activate
def test_mark_recipe_as_processed_success(mealie_client):
    """Test marking a recipe as processed."""
    recipe_slug = "test-recipe"

    # Mock getting the recipe
    responses.add(
        responses.GET,
        f"https://test.mealie.com/api/recipes/{recipe_slug}",
        json={"name": "Test Recipe", "extras": {}},
        status=200,
    )

    # Mock updating the recipe
    responses.add(
        responses.PUT,
        f"https://test.mealie.com/api/recipes/{recipe_slug}",
        status=200,
    )

    result = mealie_client.mark_recipe_as_processed(recipe_slug)

    assert result is True

    # Check that the PUT request was made with the correct data
    assert len(responses.calls) == 2
    put_call = responses.calls[1]
    if put_call.request.body:
        request_data = json.loads(put_call.request.body)
        assert request_data["extras"]["translated"] == "true"


@responses.activate
def test_get_all_recipes_pagination(mealie_client):
    """Test pagination in get_all_recipes."""
    # Mock first page
    responses.add(
        responses.GET,
        "https://test.mealie.com/api/recipes",
        json={"items": [{"id": 1, "name": "Recipe 1"}]},
        status=200,
    )

    # Mock second page (empty)
    responses.add(
        responses.GET,
        "https://test.mealie.com/api/recipes",
        json={"items": []},
        status=200,
    )

    recipes = mealie_client.get_all_recipes()

    assert len(recipes) == 1
    assert recipes[0]["name"] == "Recipe 1"


@responses.activate
def test_get_all_recipes_basic_functionality(mealie_client):
    """Test basic get_all_recipes functionality."""
    # Mock first page with recipes
    responses.add(
        responses.GET,
        "https://test.mealie.com/api/recipes",
        json={
            "items": [
                {"id": 1, "name": "Recipe 1"},
                {"id": 2, "name": "Recipe 2"},
                {"id": 3, "name": "Recipe 3"},
            ]
        },
        status=200,
    )

    # Mock second page (empty)
    responses.add(
        responses.GET,
        "https://test.mealie.com/api/recipes",
        json={"items": []},
        status=200,
    )

    recipes = mealie_client.get_all_recipes()

    # Should return all recipes since filtering is now done at processing level
    assert len(recipes) == 3
    assert recipes[0]["name"] == "Recipe 1"
    assert recipes[1]["name"] == "Recipe 2"
    assert recipes[2]["name"] == "Recipe 3"
