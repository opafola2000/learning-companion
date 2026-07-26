from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    tavily_api_key: str = ""
    jwt_secret_key: str = "change-this-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "sqlite:///./learning_companion.db"
    cors_origins: str = "http://localhost:3000"
    bedrock_sonnet_model: str = "us.anthropic.claude-sonnet-4-6"
    bedrock_haiku_model: str = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    anthropic_api_key: str = ""
    anthropic_sonnet_model: str = "claude-sonnet-4-6"
    anthropic_haiku_model: str = "claude-haiku-4-5-20251001"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
