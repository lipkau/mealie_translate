"""Factory for creating translator instances based on configuration."""

import logging
from typing import TYPE_CHECKING

# Import translator classes for runtime use and testing
from .ollama_translator import OllamaTranslator
from .openai_translator import OpenAITranslator
from .translator_interface import TranslationError, TranslatorInterface

if TYPE_CHECKING:
    from .config import Settings

logger = logging.getLogger(__name__)


class TranslatorFactory:
    """Factory for creating translator instances based on configuration."""

    @staticmethod
    def create_translator(settings: "Settings") -> TranslatorInterface:
        """Create a translator instance based on the provided settings.

        Args:
            settings: Application settings containing translator configuration

        Returns:
            Configured translator instance

        Raises:
            TranslationError: If the requested provider is not available or misconfigured
        """
        provider = settings.translator_provider.lower()
        logger.info(f"Creating translator with provider: {provider}")

        if provider == "openai":
            return TranslatorFactory._create_openai_translator(settings)
        elif provider == "ollama":
            return TranslatorFactory._create_ollama_translator(settings)
        else:
            raise TranslationError(
                f"Unsupported translator provider: {provider}. "
                f"Supported providers: openai, ollama"
            )

    @staticmethod
    def _create_openai_translator(settings: "Settings") -> TranslatorInterface:
        """Create an OpenAI translator instance.

        Args:
            settings: Application settings

        Returns:
            Configured OpenAI translator

        Raises:
            TranslationError: If OpenAI configuration is invalid
        """
        try:
            if not settings.openai_api_key:
                raise TranslationError(
                    "OpenAI API key is required but not provided", provider="openai"
                )

            translator = OpenAITranslator(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                target_language=settings.target_language,
                max_retries=settings.max_retries,
                retry_delay=int(settings.retry_delay),
            )

            # Verify the translator is available
            if not translator.is_available():
                raise TranslationError(
                    "OpenAI API is not available or misconfigured", provider="openai"
                )

            logger.info(
                f"Created OpenAI translator with model: {settings.openai_model}"
            )
            return translator

        except ImportError as e:
            raise TranslationError(
                f"Failed to import OpenAI translator: {e}", provider="openai", cause=e
            ) from e
        except Exception as e:
            raise TranslationError(
                f"Failed to create OpenAI translator: {e}", provider="openai", cause=e
            ) from e

    @staticmethod
    def _create_ollama_translator(settings: "Settings") -> TranslatorInterface:
        """Create an Ollama translator instance.

        Args:
            settings: Application settings

        Returns:
            Configured Ollama translator

        Raises:
            TranslationError: If Ollama configuration is invalid
        """
        try:
            if not settings.ollama_base_url:
                raise TranslationError(
                    "Ollama base URL is required but not provided", provider="ollama"
                )

            if not settings.ollama_model:
                raise TranslationError(
                    "Ollama model is required but not provided", provider="ollama"
                )

            translator = OllamaTranslator(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                timeout=settings.ollama_timeout,
            )

            # Verify the translator is available
            if not translator.is_available():
                raise TranslationError(
                    f"Ollama is not available at {settings.ollama_base_url} "
                    f"or model '{settings.ollama_model}' is not found",
                    provider="ollama",
                )

            logger.info(
                f"Created Ollama translator with model: {settings.ollama_model}"
            )
            return translator

        except ImportError as e:
            raise TranslationError(
                f"Failed to import Ollama translator (httpx dependency may be missing): {e}",
                provider="ollama",
                cause=e,
            ) from e
        except Exception as e:
            raise TranslationError(
                f"Failed to create Ollama translator: {e}", provider="ollama", cause=e
            ) from e

    @staticmethod
    def list_available_providers(settings: "Settings") -> list[str]:
        """List available translation providers based on current configuration.

        Args:
            settings: Application settings

        Returns:
            List of available provider names
        """
        available = []

        # Check OpenAI availability
        try:
            openai_translator = TranslatorFactory._create_openai_translator(settings)
            if openai_translator.is_available():
                available.append("openai")
        except TranslationError:
            pass

        # Check Ollama availability
        try:
            ollama_translator = TranslatorFactory._create_ollama_translator(settings)
            if ollama_translator.is_available():
                available.append("ollama")
        except TranslationError:
            pass

        return available

    @staticmethod
    def get_provider_info(settings: "Settings") -> dict[str, dict[str, str]]:
        """Get information about all translation providers.

        Args:
            settings: Application settings

        Returns:
            Dictionary with provider names as keys and info dictionaries as values
        """
        providers = {
            "openai": {
                "name": "OpenAI",
                "description": "Cloud-based AI translation using OpenAI's ChatGPT models",
                "requirements": "API key required, internet connection needed",
                "models": "gpt-4.1, gpt-4o, gpt-3.5-turbo, etc.",
            },
            "ollama": {
                "name": "Ollama",
                "description": "Local AI translation using Ollama models",
                "requirements": "Ollama server running locally, model downloaded",
                "models": "llama2, codellama, mistral, etc. (depends on installation)",
            },
        }

        # Add availability status
        available_providers = TranslatorFactory.list_available_providers(settings)
        for provider_name, provider_info in providers.items():
            provider_info["available"] = (
                "yes" if provider_name in available_providers else "no"
            )

        return providers
