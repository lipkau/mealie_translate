"""Tests for Ollama-related configuration settings."""

import pytest
from pydantic import ValidationError

from mealie_translate.config import Settings


class TestOllamaConfiguration:
    """Test Ollama-specific configuration settings."""

    def test_default_ollama_settings(self):
        """Test default Ollama configuration values."""
        settings = Settings()

        assert settings.translator_provider == "openai"  # Default provider
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.ollama_model == "llama2"
        assert settings.ollama_timeout == 60

    def test_ollama_provider_selection(self):
        """Test setting Ollama as the translator provider."""
        settings = Settings(translator_provider="ollama")

        assert settings.translator_provider == "ollama"

    def test_ollama_provider_case_insensitive(self):
        """Test that provider validation is case-insensitive."""
        settings_upper = Settings(translator_provider="OLLAMA")
        settings_mixed = Settings(translator_provider="Ollama")

        assert settings_upper.translator_provider == "ollama"
        assert settings_mixed.translator_provider == "ollama"

    def test_invalid_provider(self):
        """Test validation error for invalid provider."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(translator_provider="invalid_provider")

        error_str = str(exc_info.value)
        assert "translator_provider must be either 'openai' or 'ollama'" in error_str

    def test_ollama_url_trailing_slash_removal(self):
        """Test that trailing slashes are removed from Ollama URL."""
        settings = Settings(ollama_base_url="http://localhost:11434/")

        assert settings.ollama_base_url == "http://localhost:11434"

    def test_custom_ollama_settings(self):
        """Test custom Ollama configuration."""
        settings = Settings(
            translator_provider="ollama",
            ollama_base_url="http://custom-server:8080",
            ollama_model="mistral",
            ollama_timeout=120,
        )

        assert settings.translator_provider == "ollama"
        assert settings.ollama_base_url == "http://custom-server:8080"
        assert settings.ollama_model == "mistral"
        assert settings.ollama_timeout == 120

    def test_dry_run_default_settings(self):
        """Test default dry run configuration."""
        settings = Settings()

        assert settings.dry_run is False
        assert settings.dry_run_limit == 5

    def test_dry_run_custom_settings(self):
        """Test custom dry run configuration."""
        settings = Settings(
            dry_run=True,
            dry_run_limit=10,
        )

        assert settings.dry_run is True
        assert settings.dry_run_limit == 10

    def test_dry_run_limit_validation(self):
        """Test validation of dry run limit."""
        # Valid limit
        settings = Settings(dry_run_limit=1)
        assert settings.dry_run_limit == 1

        # Invalid limit (too small)
        with pytest.raises(ValidationError) as exc_info:
            Settings(dry_run_limit=0)

        error_str = str(exc_info.value)
        assert "dry_run_limit must be at least 1" in error_str

    def test_retry_delay_type_conversion(self):
        """Test that retry_delay is converted to int properly."""
        settings = Settings(retry_delay=2.5)

        # Should be converted to int
        assert settings.retry_delay == 2
        assert isinstance(settings.retry_delay, int)

    def test_environment_variable_loading(self):
        """Test loading settings from environment variables."""
        import os

        # Set test environment variables
        test_env = {
            "TRANSLATOR_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://test-server:9000",
            "OLLAMA_MODEL": "codellama",
            "OLLAMA_TIMEOUT": "90",
            "DRY_RUN": "true",
            "DRY_RUN_LIMIT": "15",
        }

        # Save original values
        original_env = {}
        for key in test_env:
            original_env[key] = os.environ.get(key)
            os.environ[key] = test_env[key]

        try:
            settings = Settings()

            assert settings.translator_provider == "ollama"
            assert settings.ollama_base_url == "http://test-server:9000"
            assert settings.ollama_model == "codellama"
            assert settings.ollama_timeout == 90
            assert settings.dry_run is True
            assert settings.dry_run_limit == 15

        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_mixed_provider_settings(self):
        """Test that both OpenAI and Ollama settings can coexist."""
        settings = Settings(
            translator_provider="openai",
            openai_api_key="test_openai_key",
            openai_model="gpt-4",
            ollama_base_url="http://localhost:11434",
            ollama_model="llama2",
        )

        # OpenAI settings should be preserved
        assert settings.openai_api_key == "test_openai_key"
        assert settings.openai_model == "gpt-4"

        # Ollama settings should also be preserved
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.ollama_model == "llama2"

        # Provider should determine which is used
        assert settings.translator_provider == "openai"

    def test_complete_ollama_configuration(self):
        """Test complete Ollama configuration for production use."""
        settings = Settings(
            # Provider selection
            translator_provider="ollama",
            # Mealie configuration
            mealie_base_url="https://mealie.example.com",
            mealie_api_token="test_token",
            # Ollama configuration
            ollama_base_url="http://ollama-server:11434",
            ollama_model="mistral",
            ollama_timeout=180,
            # Translation configuration
            target_language="French",
            processed_tag="translated",
            # Processing configuration
            batch_size=5,
            max_retries=2,
            retry_delay=3,
            # Dry run configuration
            dry_run=False,
            dry_run_limit=3,
        )

        # Verify all settings
        assert settings.translator_provider == "ollama"
        assert settings.mealie_base_url == "https://mealie.example.com"
        assert settings.ollama_base_url == "http://ollama-server:11434"
        assert settings.ollama_model == "mistral"
        assert settings.ollama_timeout == 180
        assert settings.target_language == "French"
        assert settings.batch_size == 5
        assert settings.max_retries == 2
        assert settings.retry_delay == 3
        assert settings.dry_run is False
        assert settings.dry_run_limit == 3
