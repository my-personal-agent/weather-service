import logging
from functools import lru_cache
from typing import Annotated

from pydantic import BeforeValidator, Field, ValidationError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    env: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    openweather_api_key: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    openweather_base_url: Annotated[str, Field(pattern=r"^https?://")]
    openweather_geo_base_url: Annotated[str, Field(pattern=r"^https?://")]
    mcp_host: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    mcp_port: Annotated[int, Field(ge=0)]

    class ConfigDict:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()  # type: ignore
    except ValidationError as e:
        logger.error("❌ Environment configuration error:")
        logger.error(e)
        raise SystemExit(1)
