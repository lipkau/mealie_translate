"""Tests for OpenAI translator integration."""

import json
from unittest.mock import Mock, patch

import pytest
from openai import OpenAI

from mealie_translate.config import Settings
from mealie_translate.openai_translator import OpenAITranslator
from mealie_translate.translator_interface import TranslationError


@pytest.fixture
def openai_settings():
    """Create settings configured for OpenAI."""
    return Settings(
        translator_provider="openai",
        openai_api_key="test_api_key",
        openai_model="gpt-4o-mini",
        target_language="English",
        max_retries=2,
        retry_delay=1,
    )


@pytest.fixture
def openai_translator(openai_settings):
    """Create an OpenAI translator instance."""
    return OpenAITranslator(
        api_key=openai_settings.openai_api_key,
        model=openai_settings.openai_model,
        target_language=openai_settings.target_language,
        max_retries=openai_settings.max_retries,
        retry_delay=openai_settings.retry_delay,
    )


class TestOpenAITranslator:
    """Test OpenAI translator functionality."""

    def test_initialization(self, openai_translator):
        """Test OpenAI translator initialization."""
        assert openai_translator.model == "gpt-4o-mini"
        assert openai_translator.target_language == "English"
        assert openai_translator.max_retries == 2
        assert openai_translator.retry_delay == 1
        assert isinstance(openai_translator.client, OpenAI)

    def test_get_provider_name(self, openai_translator):
        """Test provider name method."""
        assert openai_translator.get_provider_name() == "openai"

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_is_available_success(self, mock_openai_class, openai_translator):
        """Test is_available when OpenAI API is accessible."""
        # Mock successful OpenAI API response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "test response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        openai_translator.client = mock_client

        assert openai_translator.is_available() is True
        mock_client.chat.completions.create.assert_called_once()

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_is_available_api_error(self, mock_openai_class, openai_translator):
        """Test is_available when OpenAI API is down."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        openai_translator.client = mock_client

        assert openai_translator.is_available() is False

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_is_available_empty_response(self, mock_openai_class, openai_translator):
        """Test is_available when API returns empty response."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = None
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        openai_translator.client = mock_client

        assert openai_translator.is_available() is False

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_translate_recipe_success(self, mock_openai_class, openai_translator):
        """Test successful recipe translation."""
        # Sample recipe data - OpenAI translator expects ingredient dictionaries
        recipe_data = {
            "name": "Test Recipe",
            "description": "A simple test recipe",
            "recipeIngredient": [{"note": "2 cups flour"}, {"note": "1 lb butter"}],
            "recipeInstructions": [{"text": "Mix ingredients at 350F"}],
        }

        # Expected translated recipe - maintain dictionary format
        translated_recipe = {
            "name": "Receta de Prueba",
            "description": "Una receta de prueba simple",
            "recipeIngredient": [
                {"note": "480 ml harina"},
                {"note": "455 g mantequilla"},
            ],
            "recipeInstructions": [{"text": "Mezclar ingredientes a 175C"}],
        }

        # Mock OpenAI responses for each field translation
        mock_client = Mock()

        # Create individual responses for each field
        mock_responses = [
            self._create_mock_response("Receta de Prueba"),  # name
            self._create_mock_response("Una receta de prueba simple"),  # description
            self._create_mock_response(
                "Mezclar ingredientes a 175C"
            ),  # instructions text
            self._create_mock_response(
                "1. 480 ml harina\n2. 455 g mantequilla"
            ),  # ingredient batch
        ]
        mock_client.chat.completions.create.side_effect = mock_responses
        openai_translator.client = mock_client

        result = openai_translator.translate_recipe(recipe_data, "Spanish")

        assert result == translated_recipe

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_translate_recipe_unusual_response(
        self, mock_openai_class, openai_translator
    ):
        """Test translation with unusual but valid response."""
        recipe_data = {"name": "Test Recipe"}

        # Mock OpenAI response with unusual content
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "This is unusual response text"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        openai_translator.client = mock_client

        # Should not raise an exception - translator returns unusual text
        result = openai_translator.translate_recipe(recipe_data, "Spanish")
        assert result["name"] == "This is unusual response text"

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_translate_recipe_api_error(self, mock_openai_class, openai_translator):
        """Test translation with API error."""
        recipe_data = {"name": "Test Recipe"}

        # Mock API error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception(
            "Rate limit exceeded"
        )
        openai_translator.client = mock_client

        with pytest.raises(TranslationError) as exc_info:
            openai_translator.translate_recipe(recipe_data, "Spanish")

        assert "Failed to translate after" in str(exc_info.value)
        assert exc_info.value.provider == "openai"

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_translate_recipe_empty_response(
        self, mock_openai_class, openai_translator
    ):
        """Test translation with empty response."""
        recipe_data = {"name": "Test Recipe"}

        # Mock empty response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = ""
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        openai_translator.client = mock_client

        # Empty response returns empty string, doesn't raise error
        result = openai_translator.translate_recipe(recipe_data, "Spanish")
        assert result["name"] == ""

    @patch("mealie_translate.openai_translator.OpenAI")
    @patch("mealie_translate.openai_translator.time.sleep")
    def test_translate_recipe_with_retries(
        self, mock_sleep, mock_openai_class, openai_translator
    ):
        """Test translation with retry logic."""
        recipe_data = {"name": "Test Recipe"}

        # Mock client that fails once then succeeds (within max_retries=2)
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [
            Exception("Temporary error"),
            self._create_mock_response("Translated Recipe"),
        ]
        openai_translator.client = mock_client

        result = openai_translator.translate_recipe(recipe_data, "Spanish")

        assert result == {"name": "Translated Recipe"}
        assert mock_client.chat.completions.create.call_count == 2
        assert mock_sleep.call_count == 1  # One retry

    @patch("mealie_translate.openai_translator.OpenAI")
    @patch("mealie_translate.openai_translator.time.sleep")
    def test_translate_recipe_max_retries_exceeded(
        self, mock_sleep, mock_openai_class, openai_translator
    ):
        """Test translation when max retries are exceeded."""
        recipe_data = {"name": "Test Recipe"}

        # Mock client that always fails
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Persistent error")
        openai_translator.client = mock_client

        with pytest.raises(TranslationError) as exc_info:
            openai_translator.translate_recipe(recipe_data, "Spanish")

        assert "Failed to translate after" in str(exc_info.value)
        assert exc_info.value.provider == "openai"
        # Should try max_retries times (2 by default)
        assert (
            mock_client.chat.completions.create.call_count
            == openai_translator.max_retries
        )

    def test_system_message_content(self, openai_translator):
        """Test that system message contains translation rules."""
        system_message = openai_translator.SYSTEM_MESSAGE

        # Check that system message contains key translation concepts
        assert "recipe translator" in system_message.lower()
        assert "unit converter" in system_message.lower()
        assert "structure" in system_message.lower()

    def test_unit_conversion_rules_defined(self, openai_translator):
        """Test that unit conversion rules are properly defined."""
        rules = openai_translator.UNIT_CONVERSION_RULES

        # Check for key unit conversions
        assert "cup" in rules.lower()
        assert "fahrenheit" in rules.lower() or "celsius" in rules.lower()
        assert "ounce" in rules.lower() or "pound" in rules.lower()

    def test_translation_rules_base_defined(self, openai_translator):
        """Test that translation rules base is properly defined."""
        rules = openai_translator.TRANSLATION_RULES_BASE

        # Check for translation guidelines
        assert "translate" in rules.lower()
        assert "formatting" in rules.lower() or "format" in rules.lower()

    def _create_mock_response(self, content):
        """Helper to create a mock OpenAI response."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = content  # Return plain text, not JSON
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        return mock_response


class TestOpenAIIntegration:
    """Integration tests for OpenAI translator with other components."""

    def test_initialization_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        translator = OpenAITranslator(
            api_key="custom_key",
            model="gpt-4",
            target_language="French",
            max_retries=5,
            retry_delay=2,
        )

        assert translator.model == "gpt-4"
        assert translator.target_language == "French"
        assert translator.max_retries == 5
        assert translator.retry_delay == 2

    @patch("mealie_translate.openai_translator.OpenAI")
    def test_full_translation_workflow(self, mock_openai_class, openai_translator):
        """Test complete translation workflow."""
        # Mock availability check
        mock_client = Mock()
        availability_response = Mock()
        availability_choice = Mock()
        availability_message = Mock()
        availability_message.content = "test"
        availability_choice.message = availability_message
        availability_response.choices = [availability_choice]

        # Mock translation
        translated_recipe = {
            "name": "Receta Traducida",
            "description": "Descripción traducida",
        }
        translation_response = Mock()
        translation_choice = Mock()
        translation_message = Mock()
        translation_message.content = json.dumps(translated_recipe)
        translation_choice.message = translation_message
        translation_response.choices = [translation_choice]

        # Create mock responses for name and description
        name_response = Mock()
        name_choice = Mock()
        name_message = Mock()
        name_message.content = "Receta Traducida"
        name_choice.message = name_message
        name_response.choices = [name_choice]

        desc_response = Mock()
        desc_choice = Mock()
        desc_message = Mock()
        desc_message.content = "Descripción traducida"
        desc_choice.message = desc_message
        desc_response.choices = [desc_choice]

        mock_client.chat.completions.create.side_effect = [
            availability_response,
            name_response,  # name
            desc_response,  # description
        ]
        openai_translator.client = mock_client

        # Test availability
        assert openai_translator.is_available() is True

        # Test translation
        recipe = {"name": "Original Recipe", "description": "Original description"}
        result = openai_translator.translate_recipe(recipe, "Spanish")

        expected_result = {
            "name": "Receta Traducida",
            "description": "Descripción traducida",
        }
        assert result == expected_result
        assert mock_client.chat.completions.create.call_count == 3

    def test_error_handling_preserves_context(self, openai_translator):
        """Test that error handling preserves context information."""
        with patch("mealie_translate.openai_translator.OpenAI"):
            # Mock a specific error
            original_error = Exception("Specific OpenAI error")
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = original_error
            openai_translator.client = mock_client

            with pytest.raises(TranslationError) as exc_info:
                openai_translator.translate_recipe({"name": "test"}, "Spanish")

            # Check that the error chain is preserved (wrapped twice)
            assert isinstance(exc_info.value.cause, TranslationError)
            assert exc_info.value.provider == "openai"

    def test_exponential_backoff(self, openai_translator):
        """Test that retry delay increases exponentially."""
        with patch("mealie_translate.openai_translator.time.sleep") as mock_sleep:
            with patch("mealie_translate.openai_translator.OpenAI"):
                mock_client = Mock()
                mock_client.chat.completions.create.side_effect = Exception("Error")
                openai_translator.client = mock_client

                with pytest.raises(TranslationError):
                    openai_translator.translate_recipe({"name": "test"}, "Spanish")

                # Verify exponential backoff pattern
                sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert len(sleep_calls) == openai_translator.max_retries - 1
                # Each delay should be roughly double the previous (with some jitter)
                for i in range(1, len(sleep_calls)):
                    assert sleep_calls[i] >= sleep_calls[i - 1]

    def test_full_recipe_structure_handling(self, openai_translator):
        """Test that translator can handle complex recipe structures."""
        recipe_data = {
            "name": "Chocolate Cake",
            "description": "Delicious cake",
            "recipeIngredient": [{"note": "2 cups flour"}, {"note": "1 pound sugar"}],
            "recipeInstructions": [{"text": "Bake at 350F for 30 minutes"}],
            "notes": [{"text": "Best served warm"}],
        }

        # Test that the translator can process all fields
        with patch("mealie_translate.openai_translator.OpenAI"):
            mock_client = Mock()

            # Mock responses for each field translation
            mock_responses = []
            for _ in range(
                5
            ):  # name, description, ingredients (2), instructions, notes
                response = Mock()
                choice = Mock()
                message = Mock()
                message.content = "translated"
                choice.message = message
                response.choices = [choice]
                mock_responses.append(response)

            mock_client.chat.completions.create.side_effect = mock_responses
            openai_translator.client = mock_client

            # Should not raise an exception
            result = openai_translator.translate_recipe(recipe_data, "Spanish")
            assert result is not None
            assert "name" in result
