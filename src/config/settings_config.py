import logging
from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, BeforeValidator, Field, ValidationError, computed_field
from pydantic_settings import BaseSettings

from enums.mcp_transport import McpTransport

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    env: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]

    mcp_project_name: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    mcp_project_version: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    mcp_host: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    mcp_port: Annotated[int, Field(ge=0)]
    mcp_transport: McpTransport

    openweather_api_key: Annotated[str, BeforeValidator(str.strip), Field(min_length=1)]
    openweather_base_url: AnyHttpUrl
    openweather_geo_base_url: AnyHttpUrl

    class ConfigDict:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @computed_field
    def mcp_project_info(self) -> str:
        return f"{self.mcp_project_name} - {self.mcp_project_version}"


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()  # type: ignore
    except ValidationError as e:
        logger.error("❌ Environment configuration error:")
        logger.error(e)
        raise SystemExit(1)
