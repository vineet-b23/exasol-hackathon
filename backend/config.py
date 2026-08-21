from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    db_path: str = Field(default="ecommerce_trace.db", env="DB_PATH")
    environment: str = Field(default="development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate centrally to be imported across the application
settings = Settings()