"""Load .env configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Config:
    """Typed configuration object for Voxum."""

    # Google Drive
    google_drive_folder_id: str
    google_client_secrets_path: Path

    # LiteLLM (transcription + summarization)
    # API keys are read from environment by LiteLLM (e.g., OPENAI_API_KEY, GEMINI_API_KEY)
    transcription_model: str
    summarization_model: str

    # Resend (email)
    resend_api_key: str
    email_to: str
    email_from: str

    # App settings
    summary_language: str
    poll_interval_seconds: int


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


def load_config() -> Config:
    """Load configuration from environment variables.

    Looks for .env file in current directory or parent directories.

    Returns:
        Config: Typed configuration object

    Raises:
        ConfigError: If required configuration is missing
    """
    load_dotenv()

    missing = []

    def get_required(key: str) -> str:
        value = os.getenv(key)
        if not value:
            missing.append(key)
            return ""
        return value

    def get_optional(key: str, default: str) -> str:
        return os.getenv(key, default)

    config = Config(
        google_drive_folder_id=get_required("GOOGLE_DRIVE_FOLDER_ID"),
        google_client_secrets_path=Path(
            get_optional("GOOGLE_CLIENT_SECRETS_PATH", "client_secrets.json")
        ),
        transcription_model=get_optional("TRANSCRIPTION_MODEL", "whisper-1"),
        summarization_model=get_optional("SUMMARIZATION_MODEL", "gpt-4o-mini"),
        resend_api_key=get_required("RESEND_API_KEY"),
        email_to=get_required("EMAIL_TO"),
        email_from=get_required("EMAIL_FROM"),
        summary_language=get_optional("SUMMARY_LANGUAGE", "en"),
        poll_interval_seconds=int(get_optional("POLL_INTERVAL_SECONDS", "60")),
    )

    if missing:
        raise ConfigError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please set them in your .env file or environment."
        )

    return config


# Singleton config instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the singleton configuration instance.

    Returns:
        Config: The configuration object

    Raises:
        ConfigError: If configuration is invalid
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
