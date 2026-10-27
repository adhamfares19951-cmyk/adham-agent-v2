"""Centralized configuration loader and workspace environment manager for adham-agent.

Handles strongly-typed settings validation via Pydantic, loads .env secrets safely,
defines default model names, and guarantees workspace directories exist on startup.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field

# Determine base directory (project base or workspace root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Robust .env auto-discovery whether running from workspace root or adham-agent/
env_candidates = [
    Path.cwd() / ".env",
    Path.cwd() / "adham-agent" / ".env",
    BASE_DIR / ".env",
    BASE_DIR / "adham-agent" / ".env",
    BASE_DIR.parent / "adham-agent" / ".env",
    BASE_DIR.parent / ".env",
    Path("C:/Projects/adham-agent/.env"),
]
env_file_path: Optional[Path] = None
for candidate in env_candidates:
    if candidate.is_file():
        env_file_path = candidate
        load_dotenv(candidate, override=False)
        break

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class _BaseSettingsConfig(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=str(env_file_path) if env_file_path else ".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
        )

except ImportError:
    from pydantic import BaseModel

    class _BaseSettingsConfig(BaseModel):  # type: ignore[no-redef]
        """Fallback base when pydantic-settings is being installed."""
        pass


class Settings(_BaseSettingsConfig):
    """Centralized configuration and runtime environment validation."""

    # --------------------------------------------------------------------------
    # API Keys & Endpoints
    # --------------------------------------------------------------------------
    GEMINI_API_KEY: str = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", ""),
        description="Google Gemini API Key (Official modern google-genai SDK)",
    )
    DEEPSEEK_API_KEY: str = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENROUTER_API_KEY", ""),
        description="DeepSeek API Key (OpenAI-compatible client, supports direct DeepSeek or OpenRouter API key)",
    )
    DEEPSEEK_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL") or (
            "https://openrouter.ai/api/v1" if (not os.getenv("DEEPSEEK_API_KEY") and os.getenv("OPENROUTER_API_KEY"))
            else "https://api.deepseek.com"
        ),
        description="Base URL for DeepSeek API",
    )
    TELEGRAM_BOT_TOKEN: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN", ""),
        description="Telegram Bot API Token",
    )
    YOUTUBE_CLIENT_SECRETS_FILE: str = Field(
        default_factory=lambda: os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secret.json"),
        description="Path to YouTube OAuth2 client secrets JSON file",
    )

    # --------------------------------------------------------------------------
    # Default Dual-Model Routing
    # --------------------------------------------------------------------------
    GEMINI_MODEL: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        description="Primary model for orchestration, JSON structuring, and YouTube creative/SEO",
    )
    DEEPSEEK_MODEL: str = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODEL") or (
            "deepseek/deepseek-chat" if (not os.getenv("DEEPSEEK_API_KEY") and os.getenv("OPENROUTER_API_KEY"))
            else "deepseek-chat"
        ),
        description="Specialized engine for heavy coding, debugging, and complex technical reasoning",
    )

    # --------------------------------------------------------------------------
    # Owner Security & Bot Identity
    # --------------------------------------------------------------------------
    OWNER_ID: int = Field(
        default_factory=lambda: int(os.getenv("OWNER_ID", "0") or 0),
        description="Telegram User ID of the owner. Bot silently ignores all other users.",
    )
    TIMEZONE: str = Field(
        default_factory=lambda: os.getenv("TIMEZONE", "Asia/Gaza"),
        description="Default timezone for scheduling and reminders",
    )

    # --------------------------------------------------------------------------
    # Storage & Workspace Paths
    # --------------------------------------------------------------------------
    WORKSPACE_DATA_DIR: Path = Field(
        default_factory=lambda: BASE_DIR / "workspace_data",
        description="Base directory for runtime artifacts, logs, and state",
    )
    SQLITE_DB_PATH: Path = Field(
        default_factory=lambda: BASE_DIR / "workspace_data" / "adham_memory.db",
        description="Path to Unified SQLite database (adham_memory.db)",
    )

    @property
    def workspace_dir(self) -> Path:
        """Root workspace directory."""
        return BASE_DIR

    @property
    def youtube_ready_dir(self) -> Path:
        """Directory watched for rendered videos ready to publish."""
        return self.WORKSPACE_DATA_DIR / "youtube_ready"

    @property
    def generated_cvs_dir(self) -> Path:
        """Output directory for tailored ATS CVs and Cover Letters."""
        return self.WORKSPACE_DATA_DIR / "generated_cvs"

    @property
    def logs_dir(self) -> Path:
        """Directory for rotating system and agent execution logs."""
        return self.WORKSPACE_DATA_DIR / "logs"

    def model_post_init(self, __context: object) -> None:
        """Ensure all required workspace directories exist immediately upon initialization."""
        self.ensure_workspace_directories()

    def ensure_workspace_directories(self) -> None:
        """Creates all required workspace_data subdirectories safely on startup."""
        for directory in [
            self.WORKSPACE_DATA_DIR,
            self.youtube_ready_dir,
            self.generated_cvs_dir,
            self.logs_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Singleton settings instance ready for direct import across modules
settings = Settings()
