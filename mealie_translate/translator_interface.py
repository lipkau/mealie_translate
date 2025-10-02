"""Abstract interface for translation providers."""

from abc import ABC, abstractmethod
from typing import Any


class TranslatorInterface(ABC):
    """Abstract base class for all translation providers."""

    @abstractmethod
    def translate_recipe(
        self, recipe_data: dict[str, Any], target_language: str
    ) -> dict[str, Any]:
        """Translate a recipe to the target language.

        Args:
            recipe_data: The recipe data to translate
            target_language: The target language code (e.g., 'en', 'es', 'fr')

        Returns:
            The translated recipe data

        Raises:
            TranslationError: If translation fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the translation provider.

        Returns:
            The provider name (e.g., 'openai', 'ollama')
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the translation provider is available and properly configured.

        Returns:
            True if the provider is available, False otherwise
        """
        pass


class TranslationError(Exception):
    """Base exception for translation-related errors."""

    def __init__(
        self, message: str, provider: str | None = None, cause: Exception | None = None
    ):
        """Initialize translation error.

        Args:
            message: The error message
            provider: The provider that caused the error
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.provider = provider
        self.cause = cause

    def __str__(self) -> str:
        """Return string representation of the error."""
        base_msg = super().__str__()
        if self.provider:
            base_msg = f"[{self.provider}] {base_msg}"
        if self.cause:
            base_msg = f"{base_msg} (caused by: {self.cause})"
        return base_msg
