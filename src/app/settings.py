from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from src.common.settings import ENV_PATH

class AppSettings(BaseSettings):
    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Security (The key to access THIS server)
    MCP_SERVER_API_KEY: str | None = None
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding='utf-8',
        extra='ignore'
    )

@lru_cache()
def get_app_settings():
    return AppSettings()