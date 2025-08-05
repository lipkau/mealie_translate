"""Configuration management for the Mealie Recipe Translator."""

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Mealie Configuration
    mealie_base_url: str = ""
    mealie_api_token: str = ""

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"  # Default model, can be overridden

    # Translation Configuration
    target_language: str = "English"
    processed_tag: str = "translated"

    # Processing Configuration
    batch_size: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0

    # Scheduling Configuration (for Docker containers)
    cron_schedule: str = "0 */6 * * *"

    @field_validator("mealie_base_url")
    @classmethod
    def validate_mealie_url(cls, v):
        """Ensure Mealie URL doesn't end with a slash."""
        if v:
            return v.rstrip("/")
        return v

    @field_validator("target_language")
    @classmethod
    def validate_target_language(cls, v):
        """Ensure target language is properly formatted."""
        return v.strip().title()

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
