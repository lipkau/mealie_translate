"""Configuration management for the Mealie Recipe Translator."""

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Mealie Configuration
    mealie_base_url: str = ""
    mealie_api_token: str = ""

    # Translation Provider Configuration
    translator_provider: str = "openai"  # Options: "openai", "ollama"

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"  # Default model, can be overridden

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    ollama_timeout: int = 60

    # Translation Configuration
    target_language: str = "English"
    processed_tag: str = "translated"

    # Processing Configuration
    batch_size: int = 10
    max_retries: int = 3
    retry_delay: int | float = 1

    # Dry Run Configuration
    dry_run: bool = False
    dry_run_limit: int = 5

    # Scheduling Configuration (for Docker containers)
    cron_schedule: str = "0 */6 * * *"

    @field_validator("mealie_base_url")
    @classmethod
    def validate_mealie_url(cls, v):
        """Ensure Mealie URL doesn't end with a slash."""
        if v:
            return v.rstrip("/")
        return v

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, v):
        """Ensure Ollama URL doesn't end with a slash."""
        if v:
            return v.rstrip("/")
        return v

    @field_validator("target_language")
    @classmethod
    def validate_target_language(cls, v):
        """Ensure target language is properly formatted."""
        return v.strip().title()

    @field_validator("translator_provider")
    @classmethod
    def validate_translator_provider(cls, v):
        """Validate translator provider choice."""
        if v.lower() not in ["openai", "ollama"]:
            raise ValueError("translator_provider must be either 'openai' or 'ollama'")
        return v.lower()

    @field_validator("dry_run_limit")
    @classmethod
    def validate_dry_run_limit(cls, v):
        """Ensure dry run limit is positive."""
        if v < 1:
            raise ValueError("dry_run_limit must be at least 1")
        return v

    @field_validator("retry_delay", mode="before")
    @classmethod
    def validate_retry_delay(cls, v):
        """Convert retry_delay to int and ensure it's positive."""
        try:
            # Try to convert to float first, then int
            if isinstance(v, str):
                numeric_value = float(v)
            elif isinstance(v, int | float):
                numeric_value = float(v)
            else:
                raise ValueError("retry_delay must be a number")

            # Convert to int, but allow values less than 1 for testing
            result = int(numeric_value) if numeric_value >= 1 else 1
            return result
        except (ValueError, TypeError) as e:
            raise ValueError("retry_delay must be a valid number") from e

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
