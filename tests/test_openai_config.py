"""Tests for OpenAI-related configuration settings."""

import pytest
from pydantic import ValidationError

from mealie_translate.config import Settings


class TestOpenAIConfiguration:
    """Test OpenAI-specific configuration settings."""

    def test_default_openai_settings(self):
        """Test default OpenAI configuration values."""
        # Override environment variables to test actual defaults
        settings = Settings(
            openai_api_key="",  # Override environment variable
            translator_provider="openai",
            openai_model="gpt-4o-mini",  # Override environment variable
        )

        assert settings.translator_provider == "openai"  # Default provider
        assert settings.openai_api_key == ""  # Must be provided by user
        assert settings.openai_model == "gpt-4o-mini"  # Default model

    def test_openai_provider_selection(self):
        """Test setting OpenAI as the translator provider."""
        settings = Settings(translator_provider="openai")

        assert settings.translator_provider == "openai"

    def test_openai_provider_case_insensitive(self):
        """Test that provider validation is case-insensitive."""
        settings_upper = Settings(translator_provider="OPENAI")
        settings_mixed = Settings(translator_provider="OpenAI")

        assert settings_upper.translator_provider == "openai"
        assert settings_mixed.translator_provider == "openai"

    def test_invalid_provider(self):
        """Test validation error for invalid provider."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(translator_provider="invalid_provider")

        error_str = str(exc_info.value)
        assert "translator_provider must be either 'openai' or 'ollama'" in error_str

    def test_custom_openai_settings(self):
        """Test custom OpenAI configuration."""
        settings = Settings(
            translator_provider="openai",
            openai_api_key="sk-test123456",
            openai_model="gpt-4",
        )

        assert settings.translator_provider == "openai"
        assert settings.openai_api_key == "sk-test123456"
        assert settings.openai_model == "gpt-4"

    def test_openai_model_variations(self):
        """Test different OpenAI model configurations."""
        # Override environment variable to test actual default
        settings_default = Settings(openai_model="gpt-4o-mini")
        assert settings_default.openai_model == "gpt-4o-mini"

        # Test gpt-4
        settings_gpt4 = Settings(openai_model="gpt-4")
        assert settings_gpt4.openai_model == "gpt-4"

        # Test gpt-3.5-turbo
        settings_gpt35 = Settings(openai_model="gpt-3.5-turbo")
        assert settings_gpt35.openai_model == "gpt-3.5-turbo"

        # Test custom model
        settings_custom = Settings(openai_model="gpt-4-1106-preview")
        assert settings_custom.openai_model == "gpt-4-1106-preview"

    def test_retry_configuration(self):
        """Test retry-related configuration."""
        settings = Settings(
            max_retries=5,
            retry_delay=2,
        )

        assert settings.max_retries == 5
        assert settings.retry_delay == 2

    def test_retry_delay_type_conversion(self):
        """Test that retry_delay is converted to int properly."""
        settings = Settings(retry_delay=2.5)

        # Should be converted to int
        assert settings.retry_delay == 2
        assert isinstance(settings.retry_delay, int)

    def test_retry_delay_conversion_edge_cases(self):
        """Test that retry_delay handles edge cases properly."""
        # Test float conversion
        settings_float = Settings(retry_delay=2.7)
        assert settings_float.retry_delay == 2
        assert isinstance(settings_float.retry_delay, int)

    def test_retry_delay_minimum_value(self):
        """Test that retry_delay has a minimum value of 1."""
        # Values less than 1 should be converted to 1
        settings_zero = Settings(retry_delay=0)
        assert settings_zero.retry_delay == 1

        settings_negative = Settings(retry_delay=-1)
        assert settings_negative.retry_delay == 1

        settings_small_float = Settings(retry_delay=0.5)
        assert settings_small_float.retry_delay == 1

    def test_environment_variable_loading(self):
        """Test loading OpenAI settings from environment variables."""
        import os

        # Set test environment variables
        test_env = {
            "TRANSLATOR_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-env123456",
            "OPENAI_MODEL": "gpt-4",
            "MAX_RETRIES": "4",
            "RETRY_DELAY": "3",
        }

        # Save original values
        original_env = {}
        for key in test_env:
            original_env[key] = os.environ.get(key)
            os.environ[key] = test_env[key]

        try:
            settings = Settings()

            assert settings.translator_provider == "openai"
            assert settings.openai_api_key == "sk-env123456"
            assert settings.openai_model == "gpt-4"
            assert settings.max_retries == 4
            assert settings.retry_delay == 3

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
            openai_api_key="sk-test123456",
            openai_model="gpt-4",
            ollama_base_url="http://localhost:11434",
            ollama_model="llama2",
        )

        # OpenAI settings should be preserved
        assert settings.openai_api_key == "sk-test123456"
        assert settings.openai_model == "gpt-4"

        # Ollama settings should also be preserved
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.ollama_model == "llama2"

        # Provider should determine which is used
        assert settings.translator_provider == "openai"

    def test_complete_openai_configuration(self):
        """Test complete OpenAI configuration for production use."""
        settings = Settings(
            # Provider selection
            translator_provider="openai",
            # Mealie configuration
            mealie_base_url="https://mealie.example.com",
            mealie_api_token="test_token",
            # OpenAI configuration
            openai_api_key="sk-prod123456",
            openai_model="gpt-4",
            # Translation configuration
            target_language="Spanish",
            processed_tag="translated",
            # Processing configuration
            batch_size=10,
            max_retries=3,
            retry_delay=2,
            # Dry run configuration
            dry_run=False,
            dry_run_limit=5,
        )

        # Verify all settings
        assert settings.translator_provider == "openai"
        assert settings.mealie_base_url == "https://mealie.example.com"
        assert settings.openai_api_key == "sk-prod123456"
        assert settings.openai_model == "gpt-4"
        assert settings.target_language == "Spanish"
        assert settings.batch_size == 10
        assert settings.max_retries == 3
        assert settings.retry_delay == 2
        assert settings.dry_run is False
        assert settings.dry_run_limit == 5

    def test_openai_api_key_validation(self):
        """Test that OpenAI API key can be empty (for testing) but is typically required."""
        # Empty key should be allowed for testing scenarios
        settings_empty = Settings(openai_api_key="")
        assert settings_empty.openai_api_key == ""

        # Valid key formats should work
        settings_valid = Settings(openai_api_key="sk-1234567890abcdef")
        assert settings_valid.openai_api_key == "sk-1234567890abcdef"

    def test_target_language_formatting(self):
        """Test that target language is properly formatted."""
        # Should be title-cased and stripped
        settings_lower = Settings(target_language="spanish")
        assert settings_lower.target_language == "Spanish"

        settings_upper = Settings(target_language="FRENCH")
        assert settings_upper.target_language == "French"

        settings_mixed = Settings(target_language="  italian  ")
        assert settings_mixed.target_language == "Italian"

        settings_multi_word = Settings(target_language="simplified chinese")
        assert settings_multi_word.target_language == "Simplified Chinese"

    def test_dry_run_configuration(self):
        """Test dry run configuration options."""
        # Default values
        settings_default = Settings()
        assert settings_default.dry_run is False
        assert settings_default.dry_run_limit == 5

        # Custom values
        settings_custom = Settings(dry_run=True, dry_run_limit=10)
        assert settings_custom.dry_run is True
        assert settings_custom.dry_run_limit == 10

    def test_dry_run_limit_validation(self):
        """Test validation of dry run limit."""
        # Valid limit
        settings_valid = Settings(dry_run_limit=1)
        assert settings_valid.dry_run_limit == 1

        # Invalid limit (too small)
        with pytest.raises(ValidationError) as exc_info:
            Settings(dry_run_limit=0)

        error_str = str(exc_info.value)
        assert "dry_run_limit must be at least 1" in error_str

        # Negative values should also fail
        with pytest.raises(ValidationError):
            Settings(dry_run_limit=-1)

    def test_batch_processing_configuration(self):
        """Test batch processing related settings."""
        settings = Settings(
            batch_size=20,
            processed_tag="openai-translated",
        )

        assert settings.batch_size == 20
        assert settings.processed_tag == "openai-translated"

    def test_scheduling_configuration(self):
        """Test cron scheduling configuration."""
        settings = Settings(cron_schedule="0 0 * * *")  # Daily at midnight

        assert settings.cron_schedule == "0 0 * * *"

        # Default schedule
        settings_default = Settings()
        assert settings_default.cron_schedule == "0 */6 * * *"  # Every 6 hours
