import pytest

from config.settings_config import get_settings


class TestSettingsConfig:
    """Test suite for Settings class"""

    def test_settings_with_valid_env_vars(self, monkeypatch):
        """Test Settings creation with valid environment variables"""
        # Set up valid environment variables
        env_vars = {"MCP_HOST": "localhost", "MCP_PORT": "8080"}

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Create settings instance
        settings = get_settings()

        # Assertions
        assert settings.mcp_host == "localhost"
        assert settings.mcp_port == 8080

    def test_settings_with_env_file(self):
        """Test Settings loading from .env file"""

        settings = get_settings()

        assert settings.mcp_host == "localhost"
        assert settings.mcp_port == 3001

    def test_settings_missing_required_field(self, monkeypatch):
        """Test Settings validation error when required field is missing"""
        # Set empty MCP_HOST to trigger validation error
        monkeypatch.setenv("MCP_HOST", "")

        with pytest.raises(SystemExit) as exc_info:
            get_settings()

        assert exc_info.value.code == 1
