"""Tests for recipe organiser state tracking."""

from mealie_translate.config import Settings
from mealie_translate.organizer import RecipeOrganizer


def test_is_organised_uses_default_marker() -> None:
    """RecipeOrganizer should use the default organised extras key."""
    organizer = RecipeOrganizer(
        Settings(
            mealie_base_url="https://test.mealie.com",
            mealie_api_token="test_token",
            openai_api_key="test_key",
        )
    )

    assert organizer.is_organised({"extras": {"organised": "true"}}) is True
    assert organizer.is_organised({"extras": {"organised": "1"}}) is True
    assert organizer.is_organised({"extras": {"organised": "false"}}) is False


def test_is_organised_uses_configured_marker() -> None:
    """RecipeOrganizer should honor a custom organisation marker key."""
    organizer = RecipeOrganizer(
        Settings(
            mealie_base_url="https://test.mealie.com",
            mealie_api_token="test_token",
            openai_api_key="test_key",
            organised_tag="done_flag",
        )
    )

    assert organizer.is_organised({"extras": {"done_flag": "true"}}) is True
    assert organizer.is_organised({"extras": {"organised": "true"}}) is False


def test_mark_as_organised_uses_configured_marker() -> None:
    """RecipeOrganizer should stamp the configured organisation marker key."""
    organizer = RecipeOrganizer(
        Settings(
            mealie_base_url="https://test.mealie.com",
            mealie_api_token="test_token",
            openai_api_key="test_key",
            organised_tag="done_flag",
        )
    )
    recipe = {"name": "Test Recipe", "extras": {}}

    organizer._mark_as_organised(recipe)

    assert recipe["extras"] == {"done_flag": "true"}
