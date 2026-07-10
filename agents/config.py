from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_host: str = Field(default="0.0.0.0", alias="FRONTEND_HOST")
    frontend_port: int = Field(default=7860, alias="FRONTEND_PORT")
    backend_url: str = Field(default="http://127.0.0.1:8000", alias="BACKEND_URL")

    hotel_mcp_command: Optional[str] = Field(default=None, alias="HOTEL_MCP_COMMAND")
    flight_mcp_command: Optional[str] = Field(default=None, alias="FLIGHT_MCP_COMMAND")

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.startswith("sk-"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
