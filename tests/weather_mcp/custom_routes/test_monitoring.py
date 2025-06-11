from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from weather_mcp.custom_routes.monitoring import healthz, metrics_endpoint, readyz


class TestHealthzEndpoint:
    """Test suite for /healthz endpoint"""

    @pytest.mark.asyncio
    @patch("weather_mcp.custom_routes.monitoring.logger")
    async def test_healthz_success(self, mock_logger):
        """Test that healthz endpoint returns 200 OK with correct status"""
        # Create a mock request
        request = MagicMock(spec=Request)

        # Call the endpoint
        response = await healthz(request)

        # Assertions
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        assert response.body == b'{"status":"alive"}'

        # Verify logging
        mock_logger.debug.assert_called_once_with("Health check endpoint called")


class TestReadyzEndpoint:
    """Test suite for /readyz endpoint"""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("weather_mcp.custom_routes.monitoring.logger")
    async def test_readyz_success(self, mock_logger, mock_client_class):
        """Test readyz endpoint when OpenWeather API is available"""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(
            return_value={
                "weather": [{"main": "Clear"}],
                "name": "Tokyo",
            }
        )

        # Mock AsyncClient.get to return that response
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        # Mock the context manager behavior
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance

        # Create mock request and call endpoint
        request = MagicMock(spec=Request)
        response = await readyz(request)

        # Assertions
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        assert response.body == b'{"status":"ready"}'

        mock_logger.debug.assert_any_call("Readiness check endpoint called")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("weather_mcp.custom_routes.monitoring.logger")
    async def test_readyz_http_status_error(self, mock_logger, mock_client_class):
        """Test readyz endpoint when OpenWeather API returns HTTP error"""
        # Simulate an HTTP error from the OpenWeather API
        mock_error = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=MagicMock(status_code=400)
        )
        mock_client_class.side_effect = mock_error

        # Create a mock request
        request = MagicMock(spec=Request)
        response = await readyz(request)

        # Assertions
        assert isinstance(response, JSONResponse)
        assert response.status_code == 503
        assert response.body == b'{"status":"weather_api_unavailable"}'

        # Verify logging
        mock_logger.debug.assert_called_with("Readiness check endpoint called")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("weather_mcp.custom_routes.monitoring.logger")
    async def test_readyz_request_error(self, mock_logger, mock_client_class):
        """Test readyz endpoint when OpenWeather API has connection issues"""
        mock_error = httpx.RequestError("Connection timeout")
        mock_client_class.side_effect = mock_error

        # Create a mock request
        request = MagicMock(spec=Request)
        response = await readyz(request)

        # Assertions
        assert isinstance(response, JSONResponse)
        assert response.status_code == 503
        assert response.body == b'{"status":"error_checking_weather_api"}'

        # Verify logging
        mock_logger.debug.assert_called_with("Readiness check endpoint called")


class TestMetricsEndpoint:
    """Test suite for /metrics endpoint"""

    @pytest.fixture
    def mock_process_data(self):
        """Mock psutil.Process for testing"""
        mock_proc = MagicMock()
        mock_proc.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
        mock_proc.cpu_percent.return_value = 25.5
        return mock_proc

    @pytest.mark.asyncio
    @patch("weather_mcp.custom_routes.monitoring.logger")
    @patch("weather_mcp.custom_routes.monitoring.generate_latest")
    @patch("weather_mcp.custom_routes.monitoring.psutil.Process")
    async def test_metrics_endpoint_success(
        self, mock_psutil_process, mock_generate, mock_logger, mock_process_data
    ):
        """Test metrics endpoint returns Prometheus format metrics"""
        mock_psutil_process.return_value = mock_process_data
        mock_generate.return_value = b"# Prometheus metrics data"

        request = MagicMock(spec=Request)
        response = await metrics_endpoint(request)

        # Assertions
        assert isinstance(response, PlainTextResponse)
        assert response.body == b"# Prometheus metrics data"
        assert response.headers["content-type"] == CONTENT_TYPE_LATEST

        # Verify psutil calls
        mock_process_data.memory_info.assert_called_once()
        mock_process_data.cpu_percent.assert_called_once()

        # Verify logging
        mock_logger.debug.assert_called_once_with("Metrics endpoint called")

        # Verify generate_latest was called
        mock_generate.assert_called_once()

    @pytest.mark.asyncio
    @patch("weather_mcp.custom_routes.monitoring.memory_usage")
    @patch("weather_mcp.custom_routes.monitoring.generate_latest")
    @patch("weather_mcp.custom_routes.monitoring.psutil.Process")
    async def test_metrics_endpoint_sets_memory_usage(
        self, mock_psutil_process, mock_generate, mock_memory_gauge, mock_process_data
    ):
        """Test that metrics endpoint sets memory usage gauge"""
        mock_psutil_process.return_value = mock_process_data
        mock_generate.return_value = b""

        request = MagicMock(spec=Request)
        await metrics_endpoint(request)

        # Verify memory usage was set
        mock_memory_gauge.set.assert_called_once_with(1024 * 1024 * 100)

    @pytest.mark.asyncio
    @patch("weather_mcp.custom_routes.monitoring.cpu_usage")
    @patch("weather_mcp.custom_routes.monitoring.generate_latest")
    @patch("weather_mcp.custom_routes.monitoring.psutil.Process")
    async def test_metrics_endpoint_sets_cpu_usage(
        self, mock_psutil_process, mock_generate, mock_cpu_gauge, mock_process_data
    ):
        """Test that metrics endpoint sets CPU usage gauge"""
        mock_psutil_process.return_value = mock_process_data
        mock_generate.return_value = b""

        request = MagicMock(spec=Request)
        await metrics_endpoint(request)

        # Verify CPU usage was set
        mock_cpu_gauge.set.assert_called_once_with(25.5)
