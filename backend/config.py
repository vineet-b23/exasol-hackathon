from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Determine root directory for robust .env path resolution
ROOT_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    db_path: str = Field(default="ecommerce_trace.db", validation_alias="DB_PATH")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Updated Pydantic V2 configuration syntax
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()