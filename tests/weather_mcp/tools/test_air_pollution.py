import json
from datetime import datetime, timedelta
from unittest.mock import ANY, patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import TextContent

from enums.openweather import OpenWeatherEndpoint
from weather_mcp.server import mcp

GET_CURRENT_AIR_POLLUTION_BY_GEO = "get_current_air_pollution_by_geo"
GET_CURRENT_AIR_POLLUTION_BY_CITY = "get_current_air_pollution_by_city"
GET_FORECAST_AIR_POLLUTION_BY_GEO = "get_forecast_air_pollution_by_geo"
GET_FORECAST_AIR_POLLUTION_BY_CITY = "get_forecast_air_pollution_by_city"
GET_HISTORICAL_AIR_POLLUTION_BY_GEO = "get_historical_air_pollution_by_geo"
GET_HISTORICAL_AIR_POLLUTION_BY_CITY = "get_historical_air_pollution_by_city"


class TestAirPollutionToolsRregistration:
    """Test suite for air pollution tools registration"""

    @pytest.mark.asyncio
    async def test_air_pollution_tools_registration(self):
        import weather_mcp.tools  # noqa: F401

        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert GET_CURRENT_AIR_POLLUTION_BY_GEO in tool_names
        assert GET_CURRENT_AIR_POLLUTION_BY_CITY in tool_names
        assert GET_FORECAST_AIR_POLLUTION_BY_GEO in tool_names
        assert GET_FORECAST_AIR_POLLUTION_BY_CITY in tool_names
        assert GET_HISTORICAL_AIR_POLLUTION_BY_GEO in tool_names
        assert GET_HISTORICAL_AIR_POLLUTION_BY_CITY in tool_names


class TestGetCurrentAirPollutionByGeo:
    """Test suite for get_current_air_pollution_by_geo"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_valid_coordinates_success(
        self, mock_call_openweather_api, sample_air_pollution_response
    ):
        """Test successful weather retrieval with valid coordinates"""
        mock_call_openweather_api.return_value = sample_air_pollution_response

        result = await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_GEO,
            {"lat": 35.6762, "lon": 139.6503},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_AIR_POLLUTION,
            {"lat": 35.6762, "lon": 139.6503},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_boundary_coordinates(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test with boundary coordinate values"""
        mock_call_openweather_api.return_value = sample_weather_response

        # Test northern boundary
        await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_GEO,
            {"lat": 90.0, "lon": 0.0},
        )

        # Test southern boundary
        await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_GEO,
            {"lat": -90.0, "lon": 0.0},
        )

        # Test eastern boundary
        await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_GEO,
            {"lat": 0.0, "lon": 180.0},
        )

        # Test western boundary
        await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_GEO,
            {"lat": 0.0, "lon": -180.0},
        )

        assert mock_call_openweather_api.call_count == 4

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_high_precision_coordinates(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test with high precision coordinates"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_GEO,
            {"lat": 35.676234567, "lon": 139.650345678},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_AIR_POLLUTION,
            {"lat": 35.676234567, "lon": 139.650345678},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_latitude_validation_errors(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test latitude validation with Pydantic"""
        mock_call_openweather_api.return_value = sample_weather_response

        # Invalid latitude values that should raise ValidationError
        invalid_lats = [91.0, -91.0, 100.0, -100.0]

        for lat in invalid_lats:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic Field validation (ge=-90, le=90)
                await mcp.call_tool(
                    GET_CURRENT_AIR_POLLUTION_BY_GEO,
                    {"lat": lat, "lon": 0.0},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_longitude_validation_errors(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test longitude validation with Pydantic"""
        mock_call_openweather_api.return_value = sample_weather_response

        invalid_lons = [181.0, -181.0, 200.0, -200.0]

        for lon in invalid_lons:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic Field validation (ge=-90, le=90)
                await mcp.call_tool(
                    GET_CURRENT_AIR_POLLUTION_BY_GEO,
                    {"lat": 0.0, "lon": lon},
                )


class TestGetCurrentAirPollutionByCity:
    """Test suite for get_current_air_pollution_by_city"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_successful_geocoding_basic(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_response,
        sample_geo_response,
    ):
        """Test successful current air pollution request by city name."""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_response

        result = await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_CITY,
            {"city": "New York", "state_code": "NY", "country_code": "US"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_response

        mock_geo_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 1},
            mcp_ctx=ANY,
        )
        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_AIR_POLLUTION,
            {"lat": 40.7128, "lon": -74.006},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_unicode_city_names(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_response,
        sample_geo_response,
    ):
        """Test with Unicode city names"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_response

        unicode_cities = [
            ("東京", "JP", "JP"),
            ("北京", "CN", "CN"),
            ("São Paulo", "BR", "BR"),
            ("Москва", "RU", "RU"),
            ("القاهرة", "EG", "EG"),
        ]

        for city, state, country in unicode_cities:
            result = await mcp.call_tool(
                GET_CURRENT_AIR_POLLUTION_BY_CITY,
                {"city": city, "state_code": state, "country_code": country},
            )

            assert isinstance(result[0], TextContent)
            assert json.loads(result[0].text) == sample_air_pollution_response

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_city_name_trimming(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_response,
        sample_geo_response,
    ):
        """Test that city names are properly trimmed"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_response

        result = await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_CITY,
            {"city": "   New York   ", "state_code": "NY", "country_code": "US"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_response

        mock_geo_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 1},
            mcp_ctx=ANY,
        )
        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_AIR_POLLUTION,
            {"lat": 40.7128, "lon": -74.006},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_empty_city_name_handling(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_response,
        sample_geo_response,
    ):
        """Test handling of empty city name"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_response

        # This should be caught by Pydantic min_length=1 validation
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_CURRENT_AIR_POLLUTION_BY_CITY,
                {"city": "", "state_code": "NY", "country_code": "US"},
            )

        # Test with whitespace-only string
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_CURRENT_AIR_POLLUTION_BY_CITY,
                {"city": "   ", "state_code": "NY", "country_code": "US"},
            )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_state_code_format(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_response,
        sample_geo_response,
    ):
        """Test country code format validation"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_response

        invalid_codes = [
            "USA",
            "GB1",
            "X",
            "123",
            "gb",
        ]  # Should be 2 uppercase letters

        for code in invalid_codes:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation
                await mcp.call_tool(
                    GET_CURRENT_AIR_POLLUTION_BY_CITY,
                    {"city": "London", "state_code": code, "country_code": "UK"},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_country_code_format(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_response,
        sample_geo_response,
    ):
        """Test country code format validation"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_response

        invalid_codes = [
            "USA",
            "GB1",
            "X",
            "123",
            "gb",
        ]  # Should be 2 uppercase letters

        for code in invalid_codes:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation
                await mcp.call_tool(
                    GET_CURRENT_AIR_POLLUTION_BY_CITY,
                    {"city": "London", "state_code": "UK", "country_code": code},
                )


class TestGetForecastAirPollutionByGeo:
    """Test suite for get_forecast_air_pollution_by_geo"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_valid_coordinates_success(
        self, mock_call_openweather_api, sample_air_pollution_forecast_response
    ):
        """Test successful weather retrieval with valid coordinates"""
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        result = await mcp.call_tool(
            GET_FORECAST_AIR_POLLUTION_BY_GEO,
            {"lat": 35.6762, "lon": 139.6503},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_forecast_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.FORECAST_AIR_POLLUTION,
            {"lat": 35.6762, "lon": 139.6503},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_boundary_coordinates(
        self, mock_call_openweather_api, sample_air_pollution_forecast_response
    ):
        """Test with boundary coordinate values"""
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        # Test northern boundary
        await mcp.call_tool(
            GET_FORECAST_AIR_POLLUTION_BY_GEO,
            {"lat": 90.0, "lon": 0.0},
        )

        # Test southern boundary
        await mcp.call_tool(
            GET_FORECAST_AIR_POLLUTION_BY_GEO,
            {"lat": -90.0, "lon": 0.0},
        )

        # Test eastern boundary
        await mcp.call_tool(
            GET_FORECAST_AIR_POLLUTION_BY_GEO,
            {"lat": 0.0, "lon": 180.0},
        )

        # Test western boundary
        await mcp.call_tool(
            GET_FORECAST_AIR_POLLUTION_BY_GEO,
            {"lat": 0.0, "lon": -180.0},
        )

        assert mock_call_openweather_api.call_count == 4

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_high_precision_coordinates(
        self, mock_call_openweather_api, sample_air_pollution_forecast_response
    ):
        """Test with high precision coordinates"""
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        result = await mcp.call_tool(
            GET_FORECAST_AIR_POLLUTION_BY_GEO,
            {"lat": 35.676234567, "lon": 139.650345678},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_forecast_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.FORECAST_AIR_POLLUTION,
            {"lat": 35.676234567, "lon": 139.650345678},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_latitude_validation_errors(
        self, mock_call_openweather_api, sample_air_pollution_forecast_response
    ):
        """Test latitude validation with Pydantic"""
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        # Invalid latitude values that should raise ValidationError
        invalid_lats = [91.0, -91.0, 100.0, -100.0]

        for lat in invalid_lats:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic Field validation (ge=-90, le=90)
                await mcp.call_tool(
                    GET_FORECAST_AIR_POLLUTION_BY_GEO,
                    {"lat": lat, "lon": 0.0},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_longitude_validation_errors(
        self, mock_call_openweather_api, sample_air_pollution_forecast_response
    ):
        """Test longitude validation with Pydantic"""
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        invalid_lons = [181.0, -181.0, 200.0, -200.0]

        for lon in invalid_lons:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic Field validation (ge=-90, le=90)
                await mcp.call_tool(
                    GET_FORECAST_AIR_POLLUTION_BY_GEO,
                    {"lat": 0.0, "lon": lon},
                )


class TestGetForecastAirPollutionByCity:
    """Test suite for get_forecast_air_pollution_by_city"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_successful_geocoding_basic(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_forecast_response,
        sample_geo_response,
    ):
        """Test successful forecast air pollution request by city name."""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        result = await mcp.call_tool(
            GET_FORECAST_AIR_POLLUTION_BY_CITY,
            {"city": "New York", "state_code": "NY", "country_code": "US"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_forecast_response

        mock_geo_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 1},
            mcp_ctx=ANY,
        )
        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.FORECAST_AIR_POLLUTION,
            {"lat": 40.7128, "lon": -74.006},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_unicode_city_names(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_forecast_response,
        sample_geo_response,
    ):
        """Test with Unicode city names"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        unicode_cities = [
            ("東京", "JP", "JP"),
            ("北京", "CN", "CN"),
            ("São Paulo", "BR", "BR"),
            ("Москва", "RU", "RU"),
            ("القاهرة", "EG", "EG"),
        ]

        for city, state, country in unicode_cities:
            result = await mcp.call_tool(
                GET_CURRENT_AIR_POLLUTION_BY_CITY,
                {"city": city, "state_code": state, "country_code": country},
            )

            assert isinstance(result[0], TextContent)
            assert json.loads(result[0].text) == sample_air_pollution_forecast_response

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_city_name_trimming(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_forecast_response,
        sample_geo_response,
    ):
        """Test that city names are properly trimmed"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        result = await mcp.call_tool(
            GET_CURRENT_AIR_POLLUTION_BY_CITY,
            {"city": "   New York   ", "state_code": "NY", "country_code": "US"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_forecast_response

        mock_geo_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 1},
            mcp_ctx=ANY,
        )
        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_AIR_POLLUTION,
            {"lat": 40.7128, "lon": -74.006},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_empty_city_name_handling(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_forecast_response,
        sample_geo_response,
    ):
        """Test handling of empty city name"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        # This should be caught by Pydantic min_length=1 validation
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_CURRENT_AIR_POLLUTION_BY_CITY,
                {"city": "", "state_code": "NY", "country_code": "US"},
            )

        # Test with whitespace-only string
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_CURRENT_AIR_POLLUTION_BY_CITY,
                {"city": "   ", "state_code": "NY", "country_code": "US"},
            )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_state_code_format(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_forecast_response,
        sample_geo_response,
    ):
        """Test country code format validation"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        invalid_codes = [
            "USA",
            "GB1",
            "X",
            "123",
            "gb",
        ]  # Should be 2 uppercase letters

        for code in invalid_codes:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation
                await mcp.call_tool(
                    GET_CURRENT_AIR_POLLUTION_BY_CITY,
                    {"city": "London", "state_code": code, "country_code": "UK"},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_country_code_format(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_forecast_response,
        sample_geo_response,
    ):
        """Test country code format validation"""
        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = sample_air_pollution_forecast_response

        invalid_codes = [
            "USA",
            "GB1",
            "X",
            "123",
            "gb",
        ]  # Should be 2 uppercase letters

        for code in invalid_codes:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation
                await mcp.call_tool(
                    GET_CURRENT_AIR_POLLUTION_BY_CITY,
                    {"city": "London", "state_code": "UK", "country_code": code},
                )


class TestGetHistoryAirPollutionByGeo:
    """Test suite for get_historical_air_pollution_by_geo"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_valid_coordinates_success(
        self, mock_call_openweather_api, sample_air_pollution_historical_response
    ):
        """Test successful weather retrieval with valid coordinates"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        result = await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
            {"lat": 35.6762, "lon": 139.6503, "start": start_time, "end": end_time},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_historical_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.HISTORICAL_AIR_POLLUTION,
            {"lat": 35.6762, "lon": 139.6503, "start": start_time, "end": end_time},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_boundary_coordinates(
        self, mock_call_openweather_api, sample_air_pollution_historical_response
    ):
        """Test with boundary coordinate values"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        # Test northern boundary
        await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
            {"lat": 90.0, "lon": 0.0, "start": start_time, "end": end_time},
        )

        # Test southern boundary
        await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
            {"lat": -90.0, "lon": 0.0, "start": start_time, "end": end_time},
        )

        # Test eastern boundary
        await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
            {"lat": 0.0, "lon": 180.0, "start": start_time, "end": end_time},
        )

        # Test western boundary
        await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
            {"lat": 0.0, "lon": -180.0, "start": start_time, "end": end_time},
        )

        assert mock_call_openweather_api.call_count == 4

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_high_precision_coordinates(
        self, mock_call_openweather_api, sample_air_pollution_historical_response
    ):
        """Test with high precision coordinates"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        result = await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
            {
                "lat": 35.676234567,
                "lon": 139.650345678,
                "start": start_time,
                "end": end_time,
            },
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_historical_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.HISTORICAL_AIR_POLLUTION,
            {
                "lat": 35.676234567,
                "lon": 139.650345678,
                "start": start_time,
                "end": end_time,
            },
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_latitude_validation_errors(
        self, mock_call_openweather_api, sample_air_pollution_historical_response
    ):
        """Test latitude validation with Pydantic"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        # Invalid latitude values that should raise ValidationError
        invalid_lats = [91.0, -91.0, 100.0, -100.0]

        for lat in invalid_lats:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic Field validation (ge=-90, le=90)
                await mcp.call_tool(
                    GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
                    {"lat": lat, "lon": 0.0, "start": start_time, "end": end_time},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_longitude_validation_errors(
        self, mock_call_openweather_api, sample_air_pollution_historical_response
    ):
        """Test longitude validation with Pydantic"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        invalid_lons = [181.0, -181.0, 200.0, -200.0]

        for lon in invalid_lons:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic Field validation (ge=-90, le=90)
                await mcp.call_tool(
                    GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
                    {"lat": 0.0, "lon": lon, "start": start_time, "end": end_time},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    async def test_start_end_validation_errors(
        self, mock_call_openweather_api, sample_air_pollution_historical_response
    ):
        """Test latitude validation with Pydantic"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
                {"lat": 0.0, "lon": 0.0, "start": -1, "end": end_time},
            )

        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_HISTORICAL_AIR_POLLUTION_BY_GEO,
                {"lat": 0.0, "lon": 0.0, "start": start_time, "end": -1},
            )


class TestGetHistoricalAirPollutionByCity:
    """Test suite for get_historical_air_pollution_by_city"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_successful_geocoding_basic(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_historical_response,
        sample_geo_response,
    ):
        """Test successful historical air pollution request by city name."""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        result = await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
            {
                "city": "New York",
                "state_code": "NY",
                "country_code": "US",
                "start": start_time,
                "end": end_time,
            },
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_historical_response

        mock_geo_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 1},
            mcp_ctx=ANY,
        )
        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.HISTORICAL_AIR_POLLUTION,
            {
                "lat": 40.7128,
                "lon": -74.006,
                "start": start_time,
                "end": end_time,
            },
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_unicode_city_names(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_historical_response,
        sample_geo_response,
    ):
        """Test with Unicode city names"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        unicode_cities = [
            ("東京", "JP", "JP"),
            ("北京", "CN", "CN"),
            ("São Paulo", "BR", "BR"),
            ("Москва", "RU", "RU"),
            ("القاهرة", "EG", "EG"),
        ]

        for city, state, country in unicode_cities:
            result = await mcp.call_tool(
                GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
                {
                    "city": city,
                    "state_code": state,
                    "country_code": country,
                    "start": start_time,
                    "end": end_time,
                },
            )

            assert isinstance(result[0], TextContent)
            assert (
                json.loads(result[0].text) == sample_air_pollution_historical_response
            )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_city_name_trimming(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_historical_response,
        sample_geo_response,
    ):
        """Test that city names are properly trimmed"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        result = await mcp.call_tool(
            GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
            {
                "city": "   New York   ",
                "state_code": "NY",
                "country_code": "US",
                "start": start_time,
                "end": end_time,
            },
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_air_pollution_historical_response

        mock_geo_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 1},
            mcp_ctx=ANY,
        )
        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.HISTORICAL_AIR_POLLUTION,
            {
                "lat": 40.7128,
                "lon": -74.006,
                "start": start_time,
                "end": end_time,
            },
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_empty_city_name_handling(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_historical_response,
        sample_geo_response,
    ):
        """Test handling of empty city name"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        # This should be caught by Pydantic min_length=1 validation
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
                {
                    "city": "",
                    "state_code": "NY",
                    "country_code": "US",
                    "start": start_time,
                    "end": end_time,
                },
            )

        # Test with whitespace-only string
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
                {
                    "city": "   ",
                    "state_code": "NY",
                    "country_code": "US",
                    "start": start_time,
                    "end": end_time,
                },
            )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_state_code_format(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_historical_response,
        sample_geo_response,
    ):
        """Test country code format validation"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        invalid_codes = [
            "USA",
            "GB1",
            "X",
            "123",
            "gb",
        ]  # Should be 2 uppercase letters

        for code in invalid_codes:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation
                await mcp.call_tool(
                    GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
                    {
                        "city": "London",
                        "state_code": code,
                        "country_code": "UK",
                        "start": start_time,
                        "end": end_time,
                    },
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_country_code_format(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_historical_response,
        sample_geo_response,
    ):
        """Test country code format validation"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        invalid_codes = [
            "USA",
            "GB1",
            "X",
            "123",
            "gb",
        ]  # Should be 2 uppercase letters

        for code in invalid_codes:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation
                await mcp.call_tool(
                    GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
                    {
                        "city": "London",
                        "state_code": "UK",
                        "country_code": code,
                        "start": start_time,
                        "end": end_time,
                    },
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.air_pollution.call_openweather_api")
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_start_emd(
        self,
        mock_geo_call_openweather_api,
        mock_call_openweather_api,
        sample_air_pollution_historical_response,
        sample_geo_response,
    ):
        """Test country code format validation"""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())

        mock_geo_call_openweather_api.return_value = sample_geo_response
        mock_call_openweather_api.return_value = (
            sample_air_pollution_historical_response
        )

        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
                {
                    "city": "London",
                    "state_code": "UK",
                    "country_code": "UK",
                    "start": -1,
                    "end": end_time,
                },
            )

        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_HISTORICAL_AIR_POLLUTION_BY_CITY,
                {
                    "city": "London",
                    "state_code": "UK",
                    "country_code": "UK",
                    "start": start_time,
                    "end": -1,
                },
            )
