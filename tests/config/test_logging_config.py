from unittest.mock import mock_open, patch

import pytest
import yaml

from config.logging_config import setup_logging


class TestSetupLogging:
    """Test cases for the setup_logging function."""

    @patch("config.logging_config.yaml.safe_load", wraps=yaml.safe_load)
    def test_setup_logging_base_config_only(self, mock_yaml_load, monkeypatch):
        """Test setup_logging with only base configuration."""
        # Set environment variable for testing
        monkeypatch.setenv("ENV", "test")

        # Call the function
        setup_logging()

        # Verify that yaml.safe_load was called once (base config only)
        assert mock_yaml_load.call_count == 1

    @patch("config.logging_config.yaml.safe_load", wraps=yaml.safe_load)
    @patch("logging.config.dictConfig")
    def test_setup_logging_with_env_config(self, mock_dict_config, mock_yaml_load):
        """Test setup_logging with environment-specific override."""
        # Call the function
        setup_logging()

        # Verify that yaml.safe_load was called twice (base + override)
        assert mock_yaml_load.call_count == 2

        # Verify that dictConfig was called with merged config
        mock_dict_config.assert_called_once()
        call_args = mock_dict_config.call_args[0][0]

        assert call_args["handlers"]["console"]["formatter"] == "default"
        assert call_args["handlers"]["file"]["formatter"] == "default"
        assert call_args["loggers"]["app"]["handlers"] == ["console"]
        assert call_args["root"]["level"] == "DEBUG"
        assert call_args["root"]["handlers"] == ["console"]

    @patch("builtins.open", new_callable=mock_open)
    def test_setup_logging_base_config_not_found(self, mock_file):
        """Test setup_logging when base config file doesn't exist."""
        # Setup mocks
        mock_file.side_effect = FileNotFoundError("Config file not found")

        # Call the function and expect FileNotFoundError
        with pytest.raises(FileNotFoundError):
            setup_logging()

    @patch("config.logging_config.yaml.safe_load")
    def test_setup_logging_yaml_parse_error(self, mock_yaml_load):
        """Test setup_logging when YAML parsing fails."""
        # Setup mocks
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        # Call the function and expect YAMLError
        with pytest.raises(yaml.YAMLError):
            setup_logging()
