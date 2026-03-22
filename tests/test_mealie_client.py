"""Tests for Mealie API client."""

import pytest
import respx
from httpx import Response

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


def test_mealie_client_initialization(mock_settings):
    """Test MealieClient initialization."""
    client = MealieClient(mock_settings)

    assert client.base_url == "https://test.mealie.com"
    assert client.api_token == "test_token"


async def test_mealie_client_context_manager(mock_settings):
    """Test MealieClient async context manager."""
    async with MealieClient(mock_settings) as client:
        assert client._client is not None
        assert "Bearer test_token" in client.client.headers["Authorization"]

    assert client._client is None


async def test_mealie_client_http2_enabled(mock_settings):
    """Test MealieClient has HTTP/2 enabled."""
    async with MealieClient(mock_settings) as client:
        assert client._client is not None
        # Access internal transport to verify HTTP/2 configuration
        transport = client._client._transport
        assert hasattr(transport, "_pool")
        assert transport._pool._http2 is True  # type: ignore[union-attr]


@respx.mock
async def test_get_recipe_details_success(mock_settings):
    """Test successful recipe details retrieval."""
    recipe_slug = "test-recipe"
    mock_recipe = {
        "slug": recipe_slug,
        "name": "Test Recipe",
        "description": "A test recipe",
        "tags": [{"name": "test"}],
    }

    respx.get(f"https://test.mealie.com/api/recipes/{recipe_slug}").mock(
        return_value=Response(200, json=mock_recipe)
    )

    async with MealieClient(mock_settings) as client:
        recipe = await client.get_recipe_details(recipe_slug)

    assert recipe is not None
    assert recipe == mock_recipe
    assert recipe["name"] == "Test Recipe"


@respx.mock
async def test_get_recipe_details_not_found(mock_settings):
    """Test recipe details retrieval when recipe not found."""
    recipe_slug = "nonexistent-recipe"

    respx.get(f"https://test.mealie.com/api/recipes/{recipe_slug}").mock(
        return_value=Response(404)
    )

    async with MealieClient(mock_settings) as client:
        result = await client.get_recipe_details(recipe_slug)

    assert result is None


@respx.mock
async def test_update_recipe_success(mock_settings):
    """Test successful recipe update."""
    recipe_slug = "test-recipe"
    recipe_data = {"name": "Updated Recipe", "description": "Updated description"}

    respx.put(f"https://test.mealie.com/api/recipes/{recipe_slug}").mock(
        return_value=Response(200, json=recipe_data)
    )

    async with MealieClient(mock_settings) as client:
        result = await client.update_recipe(recipe_slug, recipe_data)

    assert result is True


def test_is_recipe_processed(mock_settings):
    """Test recipe processed status checking functionality."""
    client = MealieClient(mock_settings)

    recipe_processed = {"extras": {"translated": "true"}}
    recipe_not_processed = {"extras": {"some_other_field": "value"}}
    recipe_no_extras = {}

    assert client.is_recipe_processed(recipe_processed) is True
    assert client.is_recipe_processed(recipe_not_processed) is False
    assert client.is_recipe_processed(recipe_no_extras) is False


@respx.mock
async def test_mark_recipe_as_processed_success(mock_settings):
    """Test marking a recipe as processed."""
    recipe_slug = "test-recipe"

    respx.get(f"https://test.mealie.com/api/recipes/{recipe_slug}").mock(
        return_value=Response(200, json={"name": "Test Recipe", "extras": {}})
    )

    put_route = respx.put(f"https://test.mealie.com/api/recipes/{recipe_slug}").mock(
        return_value=Response(200, json={"name": "Test Recipe"})
    )

    async with MealieClient(mock_settings) as client:
        result = await client.mark_recipe_as_processed(recipe_slug)

    assert result is True
    assert put_route.called


@respx.mock
async def test_get_all_recipes_pagination(mock_settings):
    """Test pagination in get_all_recipes."""
    respx.get("https://test.mealie.com/api/recipes").mock(
        side_effect=[
            Response(200, json={"items": [{"id": 1, "name": "Recipe 1"}]}),
            Response(200, json={"items": []}),
        ]
    )

    async with MealieClient(mock_settings) as client:
        recipes = await client.get_all_recipes()

    assert len(recipes) == 1
    assert recipes[0]["name"] == "Recipe 1"


@respx.mock
async def test_get_all_recipes_basic_functionality(mock_settings):
    """Test basic get_all_recipes functionality."""
    respx.get("https://test.mealie.com/api/recipes").mock(
        side_effect=[
            Response(
                200,
                json={
                    "items": [
                        {"id": 1, "name": "Recipe 1"},
                        {"id": 2, "name": "Recipe 2"},
                        {"id": 3, "name": "Recipe 3"},
                    ]
                },
            ),
            Response(200, json={"items": []}),
        ]
    )

    async with MealieClient(mock_settings) as client:
        recipes = await client.get_all_recipes()

    assert len(recipes) == 3
    assert recipes[0]["name"] == "Recipe 1"
    assert recipes[1]["name"] == "Recipe 2"
    assert recipes[2]["name"] == "Recipe 3"
