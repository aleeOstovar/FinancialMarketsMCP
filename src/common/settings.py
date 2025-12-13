import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Calculate the Project Root dynamically
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent.parent

# Define the exact path to your .env file
ENV_PATH = PROJECT_ROOT / "deployments" / "env" / ".env"

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "CoinMarketCap MCP"
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_FILENAME: str = "mcp_server.jsonl"
    
    # Secrets
    COINMARKETCAP_API_KEY: str
    COINMARKETCAP_BASE_URL: str = "https://pro-api.coinmarketcap.com"
    MASSIVE_BASE_URL: str = "https://api.massive.com"
    MASSIVE_API_KEY: str
    # Forex Config
    FOREX_MAX_CONCURRENCY: int = 10  # Max simultaneous threads
    FOREX_TIMEOUT_SECONDS: int = 30  # Max time per request
    # Pydantic V2 Configuration
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),    # Uses the absolute path we calculated
        env_file_encoding='utf-8',
        extra='ignore'             # Ignores extra keys in .env
    )

@lru_cache()
def get_settings():
    if not os.path.exists(ENV_PATH):
        print(f"⚠️ WARNING: .env file not found at: {ENV_PATH}")
    
    return Settings()