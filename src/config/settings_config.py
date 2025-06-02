import logging

from pydantic import ValidationError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    env: str
    openweather_api_key: str
    openweather_base_url: str
    mcp_host: str
    mcp_port: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


try:
    settings = Settings()  # type: ignore
except ValidationError as e:
    logger.error("❌ Environment configuration error:")
    logger.error(e)
    raise SystemExit(1)
