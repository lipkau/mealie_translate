"""Tests for Ollama translator integration."""

"""Tests for Ollama translator integration."""

import json
from unittest.mock import Mock, patch

import httpx
import pytest

from mealie_translate.config import Settings
from mealie_translate.ollama_translator import OllamaTranslator
from mealie_translate.translator_interface import TranslationError


@pytest.fixture
def ollama_settings():
    """Create settings configured for Ollama."""
    return Settings(
        translator_provider="ollama",
        ollama_base_url="http://localhost:11434",
        ollama_model="llama2",
        ollama_timeout=30,
        target_language="English",
    )


@pytest.fixture
def ollama_translator(ollama_settings):
    """Create an Ollama translator instance."""
    return OllamaTranslator(
        base_url=ollama_settings.ollama_base_url,
        model=ollama_settings.ollama_model,
        timeout=ollama_settings.ollama_timeout,
    )


class TestOllamaTranslator:
    """Test Ollama translator functionality."""

    def test_initialization(self, ollama_translator):
        """Test Ollama translator initialization."""
        assert ollama_translator.base_url == "http://localhost:11434"
        assert ollama_translator.model == "llama2"
        assert ollama_translator.timeout == 30

    def test_get_provider_name(self, ollama_translator):
        """Test provider name method."""
        assert ollama_translator.get_provider_name() == "ollama"

    @patch("httpx.Client.get")
    def test_is_available_success(self, mock_get, ollama_translator):
        """Test is_available when Ollama is running and model exists."""
        # Mock successful Ollama API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "codellama"},
            ]
        }
        mock_get.return_value = mock_response

        assert ollama_translator.is_available() is True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags")

    @patch("httpx.Client.get")
    def test_is_available_server_down(self, mock_get, ollama_translator):
        """Test is_available when Ollama server is down."""
        mock_get.side_effect = httpx.RequestError("Connection failed")

        assert ollama_translator.is_available() is False

    @patch("httpx.Client.get")
    def test_is_available_model_not_found(self, mock_get, ollama_translator):
        """Test is_available when model doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "codellama"},
                {"name": "mistral"},
            ]
        }
        mock_get.return_value = mock_response

        assert ollama_translator.is_available() is False

    @patch("httpx.Client.post")
    def test_translate_recipe_success(self, mock_post, ollama_translator):
        """Test successful recipe translation."""
        # Sample recipe data
        recipe_data = {
            "name": "Test Recipe",
            "description": "A simple test recipe",
            "recipeIngredient": ["2 cups flour", "1 lb butter"],
            "recipeInstructions": [{"text": "Mix ingredients at 350F"}],
        }

        # Expected translated recipe
        translated_recipe = {
            "name": "Receta de Prueba",
            "description": "Una receta de prueba simple",
            "recipeIngredient": ["480 ml harina", "455 g mantequilla"],
            "recipeInstructions": [{"text": "Mezclar ingredientes a 175C"}],
        }

        # Mock Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": json.dumps(translated_recipe)}
        mock_post.return_value = mock_response

        result = ollama_translator.translate_recipe(recipe_data, "Spanish")

        assert result == translated_recipe
        mock_post.assert_called_once()

    @patch("httpx.Client.post")
    def test_translate_recipe_invalid_json_response(self, mock_post, ollama_translator):
        """Test translation with invalid JSON response."""
        recipe_data = {"name": "Test Recipe"}

        # Mock Ollama response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is not valid JSON"}
        mock_post.return_value = mock_response

        with pytest.raises(TranslationError) as exc_info:
            ollama_translator.translate_recipe(recipe_data, "Spanish")

        assert "Invalid JSON response from Ollama" in str(exc_info.value)
        assert exc_info.value.provider == "ollama"

    @patch("httpx.Client.post")
    def test_translate_recipe_api_error(self, mock_post, ollama_translator):
        """Test translation with API error."""
        recipe_data = {"name": "Test Recipe"}

        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(TranslationError) as exc_info:
            ollama_translator.translate_recipe(recipe_data, "Spanish")

        assert "Ollama API request failed with status 500" in str(exc_info.value)
        assert exc_info.value.provider == "ollama"

    @patch("httpx.Client.post")
    def test_translate_recipe_network_error(self, mock_post, ollama_translator):
        """Test translation with network error."""
        recipe_data = {"name": "Test Recipe"}

        # Mock network error
        mock_post.side_effect = httpx.RequestError("Connection timeout")

        with pytest.raises(TranslationError) as exc_info:
            ollama_translator.translate_recipe(recipe_data, "Spanish")

        assert "Network error communicating with Ollama" in str(exc_info.value)
        assert exc_info.value.provider == "ollama"

    @patch("httpx.Client.post")
    def test_translate_recipe_empty_response(self, mock_post, ollama_translator):
        """Test translation with empty response."""
        recipe_data = {"name": "Test Recipe"}

        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        with pytest.raises(TranslationError) as exc_info:
            ollama_translator.translate_recipe(recipe_data, "Spanish")

        assert "Empty response from Ollama" in str(exc_info.value)
        assert exc_info.value.provider == "ollama"

    def test_create_translation_prompt(self, ollama_translator):
        """Test translation prompt creation."""
        recipe_data = {"name": "Test Recipe", "recipeIngredient": ["2 cups flour"]}

        prompt = ollama_translator._create_translation_prompt(recipe_data, "Spanish")

        assert "Spanish" in prompt
        assert "Test Recipe" in prompt
        assert "2 cups flour" in prompt
        assert "imperial units" in prompt.lower()
        assert "metric equivalents" in prompt.lower()
        assert "JSON only" in prompt

    def test_destructor_closes_client(self):
        """Test that destructor properly closes HTTP client."""
        translator = OllamaTranslator("http://localhost:11434", "llama2", 60)
        mock_client = Mock()
        translator._client = mock_client

        # Trigger destructor
        del translator

        mock_client.close.assert_called_once()


class TestOllamaIntegration:
    """Integration tests for Ollama translator with other components."""

    def test_url_validation(self):
        """Test URL validation removes trailing slashes."""
        translator = OllamaTranslator("http://localhost:11434/", "llama2", 60)
        assert translator.base_url == "http://localhost:11434"

    @patch("httpx.Client.get")
    @patch("httpx.Client.post")
    def test_full_translation_workflow(self, mock_post, mock_get, ollama_translator):
        """Test complete translation workflow."""
        # Mock availability check
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "llama2"}]}
        mock_get.return_value = mock_get_response

        # Mock translation
        translated_recipe = {
            "name": "Receta Traducida",
            "description": "Descripción traducida",
        }
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "response": json.dumps(translated_recipe)
        }
        mock_post.return_value = mock_post_response

        # Test availability
        assert ollama_translator.is_available() is True

        # Test translation
        recipe = {"name": "Original Recipe", "description": "Original description"}
        result = ollama_translator.translate_recipe(recipe, "Spanish")

        assert result == translated_recipe
        assert mock_get.called
        assert mock_post.called

    def test_error_handling_preserves_context(self, ollama_translator):
        """Test that error handling preserves context information."""
        with patch("httpx.Client.post") as mock_post:
            # Mock a specific error
            original_error = httpx.ConnectError("Connection refused")
            mock_post.side_effect = original_error

            with pytest.raises(TranslationError) as exc_info:
                ollama_translator.translate_recipe({"name": "test"}, "Spanish")

            # Check that the original error is preserved
            assert exc_info.value.cause == original_error
            assert exc_info.value.provider == "ollama"
