from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from config.settings_config import get_settings
from enums.openweather import OpenWeatherEndpoint
from weather_mcp.utils import call_openweather_api


class TestCallOpenWeatherApi:
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_weather_api_call(
        self, mock_client, mock_context, sample_weather_response
    ):
        """Test successful API call to weather endpoint."""
        params = {"q": "London", "lang": "en"}

        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_weather_response
        mock_response.raise_for_status = MagicMock()

        # Mock the async context manager
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await call_openweather_api(
            OpenWeatherEndpoint.CURRENT_WEATHER, params, mock_context
        )

        # Verify the result
        assert result == sample_weather_response

        # Verify context logging calls
        mock_context.info.assert_any_call(
            "Calling OpenWeather API",
            params=params,
            extra={
                "request_id": mock_context.request_id,
                "client_id": mock_context.client_id,
            },
        )
        mock_context.info.assert_any_call(
            "OpenWeather API response",
            data=sample_weather_response,
            extra={
                "request_id": mock_context.request_id,
                "client_id": mock_context.client_id,
            },
        )

        # Verify progress reporting
        assert mock_context.report_progress.call_count == 4
        mock_context.report_progress.assert_any_call(
            10, total=100, message="Preparing OpenWeather API request"
        )
        mock_context.report_progress.assert_any_call(
            30, total=100, message="Calling OpenWeather API request"
        )
        mock_context.report_progress.assert_any_call(
            80, total=100, message="OpenWeather API request completed"
        )
        mock_context.report_progress.assert_any_call(
            100, total=100, message="OpenWeather API call successful"
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_geocoding_endpoint_uses_correct_base_url(
        self, mock_client, mock_context
    ):
        """Test that geocoding endpoints use the geo base URL."""
        params = {"q": "London"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "London", "lat": 51.5085, "lon": -0.1257}
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await call_openweather_api(
            OpenWeatherEndpoint.DIRECT_GEOCODING, params, mock_context
        )

        # Verify the correct URL was constructed
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()
        call_args = mock_client.return_value.__aenter__.return_value.get.call_args

        # The URL should contain the geo base URL
        assert (
            call_args[0][0]
            == get_settings().openweather_geo_base_url.rstrip("/") + "/direct"
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_api_key_and_units_added_automatically(
        self, mock_client, mock_context, sample_weather_response
    ):
        """Test that API key and units are added automatically."""
        params = {"q": "London"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_weather_response
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await call_openweather_api(
            OpenWeatherEndpoint.CURRENT_WEATHER, params, mock_context
        )

        # Verify API key and units were added
        call_args = mock_client.return_value.__aenter__.return_value.get.call_args
        expected_params = {
            "q": "London",
            "appid": get_settings().openweather_api_key,
            "units": "metric",
        }
        assert call_args[1]["params"] == expected_params

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_custom_units_preserved(
        self, mock_client, mock_context, sample_weather_response
    ):
        """Test that custom units parameter is preserved."""
        params = {"q": "London", "units": "imperial"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_weather_response
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        await call_openweather_api(
            OpenWeatherEndpoint.CURRENT_WEATHER, params, mock_context
        )

        # Verify custom units were preserved
        call_args = mock_client.return_value.__aenter__.return_value.get.call_args
        expected_params = {
            "q": "London",
            "appid": get_settings().openweather_api_key,
            "units": "imperial",  # Should preserve custom units
        }
        assert call_args[1]["params"] == expected_params

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_404_error_handling(self, mock_client, mock_context):
        """Test handling of 404 HTTP errors."""
        params = {"q": "NonexistentCity"}

        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "city not found"

        http_error = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = http_error

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        with pytest.raises(
            ToolError, match="Weather data not found for the given location"
        ):
            await call_openweather_api(
                OpenWeatherEndpoint.CURRENT_WEATHER, params, mock_context
            )

        # Verify warning was logged
        mock_context.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_500_error_handling(self, mock_client, mock_context):
        """Test handling of 500 HTTP errors."""
        params = {"q": "London"}

        # Mock 500 response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "internal server error"

        http_error = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = http_error

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        with pytest.raises(ToolError, match="Weather service returned an error"):
            await call_openweather_api(
                OpenWeatherEndpoint.CURRENT_WEATHER, params, mock_context
            )

        # Verify warning was logged
        mock_context.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_network_error_handling(self, mock_client, mock_context):
        """Test handling of network/connection errors."""
        params = {"q": "London"}

        # Mock network error
        network_error = httpx.RequestError("Connection failed")
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=network_error
        )

        with pytest.raises(ToolError, match="An unexpected error occurred"):
            await call_openweather_api(
                OpenWeatherEndpoint.CURRENT_WEATHER, params, mock_context
            )

        # Verify error was logged
        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_timeout_configuration(
        self, mock_client_class, mock_context, sample_weather_response
    ):
        """Test that HTTP client is configured with correct timeout."""
        params = {"q": "London"}

        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_weather_response
        mock_response.raise_for_status = MagicMock()

        mock_client_instance.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        mock_client_class.return_value = mock_client_instance

        await call_openweather_api(
            OpenWeatherEndpoint.CURRENT_WEATHER, params, mock_context
        )

        # Verify client was created with correct timeout
        mock_client_class.assert_called_once_with(timeout=2.0)
