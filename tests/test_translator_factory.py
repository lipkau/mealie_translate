"""Tests for translator factory functionality."""

from unittest.mock import Mock, patch

import pytest

from mealie_translate.config import Settings
from mealie_translate.translator_factory import TranslatorFactory
from mealie_translate.translator_interface import TranslationError


@pytest.fixture
def openai_settings():
    """Create settings configured for OpenAI."""
    return Settings(
        translator_provider="openai",
        openai_api_key="test_key",
        openai_model="gpt-4",
        target_language="English",
    )


@pytest.fixture
def ollama_settings():
    """Create settings configured for Ollama."""
    return Settings(
        translator_provider="ollama",
        ollama_base_url="http://localhost:11434",
        ollama_model="llama2",
        target_language="Spanish",
    )


class TestTranslatorFactory:
    """Test translator factory functionality."""

    @patch("mealie_translate.translator_factory.OpenAITranslator")
    def test_create_openai_translator(self, mock_openai_class, openai_settings):
        """Test creating OpenAI translator."""
        mock_translator = Mock()
        mock_translator.is_available.return_value = True
        mock_openai_class.return_value = mock_translator

        result = TranslatorFactory.create_translator(openai_settings)

        assert result == mock_translator
        mock_openai_class.assert_called_once_with(
            api_key="test_key",
            model="gpt-4",
            target_language="English",
            max_retries=3,
            retry_delay=1,
        )

    @patch("mealie_translate.translator_factory.OllamaTranslator")
    def test_create_ollama_translator(self, mock_ollama_class, ollama_settings):
        """Test creating Ollama translator."""
        mock_translator = Mock()
        mock_translator.is_available.return_value = True
        mock_ollama_class.return_value = mock_translator

        result = TranslatorFactory.create_translator(ollama_settings)

        assert result == mock_translator
        mock_ollama_class.assert_called_once_with(
            base_url="http://localhost:11434",
            model="llama2",
            timeout=60,
        )

    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        # Create valid settings first
        settings = Settings(translator_provider="openai", openai_api_key="test")
        # Then manually change the provider to test factory logic
        settings.translator_provider = "unsupported"

        with pytest.raises(TranslationError) as exc_info:
            TranslatorFactory.create_translator(settings)

        assert "Unsupported translator provider: unsupported" in str(exc_info.value)

    @patch("mealie_translate.translator_factory.OpenAITranslator")
    def test_openai_missing_api_key(self, mock_openai_class, openai_settings):
        """Test OpenAI translator creation with missing API key."""
        openai_settings.openai_api_key = ""

        with pytest.raises(TranslationError) as exc_info:
            TranslatorFactory.create_translator(openai_settings)

        assert "OpenAI API key is required" in str(exc_info.value)
        assert exc_info.value.provider == "openai"

    @patch("mealie_translate.translator_factory.OllamaTranslator")
    def test_ollama_missing_base_url(self, mock_ollama_class, ollama_settings):
        """Test Ollama translator creation with missing base URL."""
        ollama_settings.ollama_base_url = ""

        with pytest.raises(TranslationError) as exc_info:
            TranslatorFactory.create_translator(ollama_settings)

        assert "Ollama base URL is required" in str(exc_info.value)
        assert exc_info.value.provider == "ollama"

    @patch("mealie_translate.translator_factory.OllamaTranslator")
    def test_ollama_missing_model(self, mock_ollama_class, ollama_settings):
        """Test Ollama translator creation with missing model."""
        ollama_settings.ollama_model = ""

        with pytest.raises(TranslationError) as exc_info:
            TranslatorFactory.create_translator(ollama_settings)

        assert "Ollama model is required" in str(exc_info.value)
        assert exc_info.value.provider == "ollama"

    @patch("mealie_translate.translator_factory.OpenAITranslator")
    def test_openai_not_available(self, mock_openai_class, openai_settings):
        """Test OpenAI translator when service is not available."""
        mock_translator = Mock()
        mock_translator.is_available.return_value = False
        mock_openai_class.return_value = mock_translator

        with pytest.raises(TranslationError) as exc_info:
            TranslatorFactory.create_translator(openai_settings)

        assert "OpenAI API is not available" in str(exc_info.value)
        assert exc_info.value.provider == "openai"

    @patch("mealie_translate.translator_factory.OllamaTranslator")
    def test_ollama_not_available(self, mock_ollama_class, ollama_settings):
        """Test Ollama translator when service is not available."""
        mock_translator = Mock()
        mock_translator.is_available.return_value = False
        mock_ollama_class.return_value = mock_translator

        with pytest.raises(TranslationError) as exc_info:
            TranslatorFactory.create_translator(ollama_settings)

        assert "Ollama is not available" in str(exc_info.value)
        assert exc_info.value.provider == "ollama"

    def test_import_error_handling(self, openai_settings):
        """Test handling of import errors."""
        with patch(
            "mealie_translate.translator_factory.OpenAITranslator",
            side_effect=ImportError("Module not found"),
        ):
            with pytest.raises(TranslationError) as exc_info:
                TranslatorFactory.create_translator(openai_settings)

            assert "Failed to import OpenAI translator" in str(exc_info.value)
            assert exc_info.value.provider == "openai"

    @patch(
        "mealie_translate.translator_factory.TranslatorFactory._create_openai_translator"
    )
    @patch(
        "mealie_translate.translator_factory.TranslatorFactory._create_ollama_translator"
    )
    def test_list_available_providers(self, mock_create_ollama, mock_create_openai):
        """Test listing available providers."""
        # Mock OpenAI as available
        mock_openai = Mock()
        mock_openai.is_available.return_value = True
        mock_create_openai.return_value = mock_openai

        # Mock Ollama as not available
        mock_create_ollama.side_effect = TranslationError("Not available")

        settings = Settings()
        available = TranslatorFactory.list_available_providers(settings)

        assert "openai" in available
        assert "ollama" not in available

    def test_get_provider_info(self):
        """Test getting provider information."""
        settings = Settings()

        with patch.object(
            TranslatorFactory, "list_available_providers", return_value=["openai"]
        ):
            info = TranslatorFactory.get_provider_info(settings)

            assert "openai" in info
            assert "ollama" in info

            # Check structure
            assert "name" in info["openai"]
            assert "description" in info["openai"]
            assert "requirements" in info["openai"]
            assert "models" in info["openai"]
            assert "available" in info["openai"]

            # Check availability
            assert info["openai"]["available"] == "yes"
            assert info["ollama"]["available"] == "no"


class TestProviderSwitching:
    """Test switching between providers."""

    @patch("mealie_translate.translator_factory.OpenAITranslator")
    @patch("mealie_translate.translator_factory.OllamaTranslator")
    def test_switch_from_openai_to_ollama(self, mock_ollama_class, mock_openai_class):
        """Test switching translator providers."""
        # Setup mocks
        mock_openai = Mock()
        mock_openai.is_available.return_value = True
        mock_openai_class.return_value = mock_openai

        mock_ollama = Mock()
        mock_ollama.is_available.return_value = True
        mock_ollama_class.return_value = mock_ollama

        # Test OpenAI
        openai_settings = Settings(translator_provider="openai", openai_api_key="test")
        openai_translator = TranslatorFactory.create_translator(openai_settings)
        assert openai_translator == mock_openai

        # Test Ollama
        ollama_settings = Settings(
            translator_provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="llama2",
        )
        ollama_translator = TranslatorFactory.create_translator(ollama_settings)
        assert ollama_translator == mock_ollama

        # Verify different instances
        assert openai_translator != ollama_translator

    def test_case_insensitive_provider_names(self):
        """Test that provider names are case-insensitive."""
        settings_upper = Settings(translator_provider="OPENAI", openai_api_key="test")
        settings_mixed = Settings(translator_provider="OpenAI", openai_api_key="test")

        with patch(
            "mealie_translate.translator_factory.OpenAITranslator"
        ) as mock_class:
            mock_translator = Mock()
            mock_translator.is_available.return_value = True
            mock_class.return_value = mock_translator

            # Both should work
            TranslatorFactory.create_translator(settings_upper)
            TranslatorFactory.create_translator(settings_mixed)

            # Should have been called twice
            assert mock_class.call_count == 2


class TestErrorHandling:
    """Test comprehensive error handling."""

    def test_exception_chaining(self, openai_settings):
        """Test that exceptions are properly chained."""
        original_error = Exception("Original error")

        with patch(
            "mealie_translate.translator_factory.OpenAITranslator",
            side_effect=original_error,
        ):
            with pytest.raises(TranslationError) as exc_info:
                TranslatorFactory.create_translator(openai_settings)

            # Check exception chaining
            assert exc_info.value.cause == original_error
            assert "Failed to create OpenAI translator" in str(exc_info.value)

    def test_missing_httpx_dependency(self, ollama_settings):
        """Test handling when httpx is not available for Ollama."""
        with patch(
            "mealie_translate.translator_factory.OllamaTranslator",
            side_effect=ImportError("No module named 'httpx'"),
        ):
            with pytest.raises(TranslationError) as exc_info:
                TranslatorFactory.create_translator(ollama_settings)

            assert "httpx dependency may be missing" in str(exc_info.value)
            assert exc_info.value.provider == "ollama"
