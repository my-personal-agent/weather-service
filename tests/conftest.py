import pytest

from config.settings_config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Automatically clear the settings cache before each test"""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
