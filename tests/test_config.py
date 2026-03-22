"""Tests for configuration management."""

import os

from mealie_translate.config import Settings, get_settings


def test_module_imports():
    """Test that all modules can be imported successfully."""
    assert True


def test_settings_creation():
    """Test that Settings can be created with defaults."""
    settings = Settings()
    assert settings.target_language == "English"
    assert settings.processed_tag == "translated"
    assert settings.batch_size == 10
    assert settings.max_retries == 3
    assert settings.retry_delay == 1.0
    assert settings.max_concurrent_requests == 5
    assert settings.max_concurrent_translations == 3


def test_settings_validation():
    """Test settings validation."""
    settings = Settings(
        mealie_base_url="https://example.com/",
        mealie_api_token="test_token",
        openai_api_key="test_key",
    )

    assert settings.mealie_base_url == "https://example.com"

    settings_with_lowercase = Settings(
        mealie_base_url="https://example.com",
        mealie_api_token="test_token",
        openai_api_key="test_key",
        target_language="spanish",
    )
    assert settings_with_lowercase.target_language == "Spanish"


def test_get_settings():
    """Test that get_settings returns a Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)


def test_settings_environment_loading():
    """Test that settings can load from environment variables."""
    test_env = {
        "MEALIE_BASE_URL": "https://test.example.com",
        "MEALIE_API_TOKEN": "test_token",
        "OPENAI_API_KEY": "test_key",
        "TARGET_LANGUAGE": "spanish",
        "PROCESSED_TAG": "test_tag",
    }

    original_env = {}
    for key in test_env:
        original_env[key] = os.environ.get(key)
        os.environ[key] = test_env[key]

    try:
        settings = Settings()
        assert settings.mealie_base_url == "https://test.example.com"
        assert settings.mealie_api_token == "test_token"
        assert settings.openai_api_key == "test_key"
        assert settings.target_language == "Spanish"
        assert settings.processed_tag == "test_tag"
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
