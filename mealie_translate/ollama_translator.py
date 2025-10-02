"""Ollama-based translation provider implementation."""

import json
import logging
from typing import Any

import httpx

from .translator_interface import TranslationError, TranslatorInterface

logger = logging.getLogger(__name__)


class OllamaTranslator(TranslatorInterface):
    """Translator implementation using Ollama for local AI inference."""

    def __init__(self, base_url: str, model: str, timeout: int = 60):
        """Initialize the Ollama translator.

        Args:
            base_url: The base URL for the Ollama API (e.g., 'http://localhost:11434')
            model: The name of the model to use for translation
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def __del__(self):
        """Close the HTTP client when the translator is destroyed."""
        if hasattr(self, "_client"):
            self._client.close()

    def get_provider_name(self) -> str:
        """Get the name of the translation provider."""
        return "ollama"

    def is_available(self) -> bool:
        """Check if Ollama is available and the model is accessible.

        Returns:
            True if Ollama is available and the model exists, False otherwise
        """
        try:
            # Check if Ollama is running by attempting to list models
            response = self._client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                logger.warning(f"Ollama API not available at {self.base_url}")
                return False

            # Check if the specified model exists
            models_data = response.json()
            available_models = [
                model["name"] for model in models_data.get("models", [])
            ]

            if self.model not in available_models:
                logger.warning(
                    f"Model '{self.model}' not found in Ollama. "
                    f"Available models: {', '.join(available_models)}"
                )
                return False

            return True

        except httpx.RequestError as e:
            logger.warning(f"Failed to connect to Ollama at {self.base_url}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Error checking Ollama availability: {e}")
            return False

    def translate_recipe(
        self, recipe_data: dict[str, Any], target_language: str
    ) -> dict[str, Any]:
        """Translate a recipe using Ollama.

        Args:
            recipe_data: The recipe data to translate
            target_language: The target language code

        Returns:
            The translated recipe data

        Raises:
            TranslationError: If translation fails
        """
        try:
            # Create the translation prompt
            prompt = self._create_translation_prompt(recipe_data, target_language)

            # Make the request to Ollama
            payload = {"model": self.model, "prompt": prompt, "stream": False}

            logger.debug(f"Sending translation request to Ollama model '{self.model}'")
            response = self._client.post(f"{self.base_url}/api/generate", json=payload)

            if response.status_code != 200:
                raise TranslationError(
                    f"Ollama API request failed with status {response.status_code}: {response.text}",
                    provider="ollama",
                )

            # Parse the response
            response_data = response.json()
            translated_text = response_data.get("response", "").strip()

            if not translated_text:
                raise TranslationError("Empty response from Ollama", provider="ollama")

            # Parse the JSON response from the model
            try:
                translated_recipe = json.loads(translated_text)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse Ollama response as JSON: {translated_text}"
                )
                raise TranslationError(
                    f"Invalid JSON response from Ollama: {e}",
                    provider="ollama",
                    cause=e,
                ) from e

            # Validate the translated recipe structure
            if not isinstance(translated_recipe, dict):
                raise TranslationError(
                    "Ollama returned non-dictionary response", provider="ollama"
                )

            logger.info(
                f"Successfully translated recipe '{recipe_data.get('name', 'Unknown')}' to {target_language}"
            )
            return translated_recipe

        except httpx.RequestError as e:
            raise TranslationError(
                f"Network error communicating with Ollama: {e}",
                provider="ollama",
                cause=e,
            ) from e
        except TranslationError:
            # Re-raise translation errors as-is
            raise
        except Exception as e:
            raise TranslationError(
                f"Unexpected error during translation: {e}", provider="ollama", cause=e
            ) from e

    def _create_translation_prompt(
        self, recipe_data: dict[str, Any], target_language: str
    ) -> str:
        """Create a translation prompt for the Ollama model.

        Args:
            recipe_data: The recipe data to translate
            target_language: The target language code

        Returns:
            The formatted prompt string
        """
        # Convert recipe data to JSON for the prompt
        recipe_json = json.dumps(recipe_data, indent=2, ensure_ascii=False)

        # Create a comprehensive prompt for translation
        prompt = f"""You are a professional recipe translator. Your task is to translate the following recipe from its current language to {target_language}.

IMPORTANT INSTRUCTIONS:
1. Translate ALL text fields (name, description, instructions, ingredients, etc.)
2. Convert imperial units (cups, tablespoons, ounces, fahrenheit) to metric equivalents (ml, grams, celsius)
3. Preserve the exact JSON structure and field names
4. Keep numerical values accurate during unit conversions
5. Maintain cooking terminology appropriate for the target language
6. Return ONLY valid JSON, no additional text or explanations

RECIPE TO TRANSLATE:
{recipe_json}

TRANSLATED RECIPE (JSON only):"""

        return prompt
