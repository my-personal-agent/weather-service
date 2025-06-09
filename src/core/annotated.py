from typing import Annotated, Optional

from pydantic import BeforeValidator, Field

ANNOTATED_CITY = Annotated[
    str,
    BeforeValidator(str.strip),
    Field(
        min_length=1,
        description="City name (e.g., 'London', 'New York', 'São Paulo', '東京'). Case-insensitive, supports Unicode characters and diacritics. Can include state/province for US/CA cities (e.g., 'Austin,TX').",
    ),
]

ANNOTATED_STATE_CODE = Annotated[
    str,
    Field(
        description="Country code in ISO 3166-1 alpha-2 format (e.g., 'US', 'GB', 'JP')",
        pattern=r"^[A-Z]{2}$",
    ),
]

ANNOTATED_OPTIONAL_COUNTRY_CODE = Annotated[
    Optional[str],
    Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'JP'). Strongly recommended for cities with duplicate names. Helps ensure forecast accuracy for intended location. Defaults to None (global search, returns best match).",
        pattern=r"^[A-Z]{2}$",
    ),
]

ANNOTATED_COUNTRY_CODE = Annotated[
    str,
    Field(
        description="Country code in ISO 3166-1 alpha-2 format (e.g., 'US', 'GB', 'JP')",
        pattern=r"^[A-Z]{2}$",
    ),
]

ANNOTATED_LAT = Annotated[
    float,
    Field(
        ge=-90,
        le=90,
        description="Latitude coordinate (-90 to 90) where positive values indicate North and negative values indicate South. Higher precision (4+ decimal places) provides more accurate location matching.",
    ),
]

ANNOTATED_LON = Annotated[
    float,
    Field(
        ge=-180,
        le=180,
        description="Longitude coordinate (-180 to 180) where positive values indicate East and negative values indicate West. Higher precision (4+ decimal places) provides more accurate location matching.",
    ),
]

ANNOTATED_LANG = Annotated[
    str,
    Field(
        default="en",
        pattern=r"^[a-z]{2}$",
        description="Language code (ISO 639-1) for weather descriptions. Defaults to 'en'.",
    ),
]
