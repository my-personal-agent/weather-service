import json
from unittest.mock import ANY, patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import TextContent

from enums.openweather import OpenWeatherEndpoint
from weather_mcp.server import mcp

GET_GEO_BY_LOCATION = "get_geo_by_location"
GET_LOCATOPN_BY_GEO = "get_localtion_by_geo"


class TestGeocidingToolsRregistration:
    """Test suite for geocoding tools registration"""

    @pytest.mark.asyncio
    async def test_current_weather_tools_registration(self):
        import weather_mcp.tools  # noqa: F401

        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert GET_GEO_BY_LOCATION in tool_names
        assert GET_LOCATOPN_BY_GEO in tool_names


class TestDirectGeoByLocation:
    """Test suite for get_geo_by_location function."""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_successful_geocoding_basic(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test successful geocoding with basic parameters."""
        mock_call_openweather_api.return_value = sample_geocoding_response

        result = await mcp.call_tool(
            GET_GEO_BY_LOCATION,
            {"city": "New York", "state_code": "NY", "country_code": "US"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_geocoding_response[0]

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 5},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_geocoding_with_custom_limit(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test geocoding with custom limit parameter."""
        mock_call_openweather_api.return_value = sample_geocoding_response

        result = await mcp.call_tool(
            GET_GEO_BY_LOCATION,
            {"city": "London", "state_code": "UK", "country_code": "GB", "limit": 1},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_geocoding_response[0]

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "London,UK,GB", "limit": 1},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_unicode_city_names(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test with Unicode city names"""
        mock_call_openweather_api.return_value = sample_geocoding_response

        unicode_cities = [
            ("東京", "JP", "JP"),
            ("北京", "CN", "CN"),
            ("São Paulo", "BR", "BR"),
            ("Москва", "RU", "RU"),
            ("القاهرة", "EG", "EG"),
        ]

        for city, state, country in unicode_cities:
            result = await mcp.call_tool(
                GET_GEO_BY_LOCATION,
                {"city": city, "state_code": state, "country_code": country},
            )

            assert isinstance(result[0], TextContent)
            assert json.loads(result[0].text) == sample_geocoding_response[0]

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_city_name_trimming(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test that city names are properly trimmed"""
        mock_call_openweather_api.return_value = sample_geocoding_response

        result = await mcp.call_tool(
            GET_GEO_BY_LOCATION,
            {"city": "   New York   ", "state_code": "NY", "country_code": "US"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_geocoding_response[0]

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.DIRECT_GEOCODING,
            {"q": "New York,NY,US", "limit": 5},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_empty_city_name_handling(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test handling of empty city name"""
        mock_call_openweather_api.return_value = sample_geocoding_response

        # This should be caught by Pydantic min_length=1 validation
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_GEO_BY_LOCATION,
                {"city": "", "state_code": "NY", "country_code": "US"},
            )

        # Test with whitespace-only string
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_GEO_BY_LOCATION,
                {"city": "   ", "state_code": "NY", "country_code": "US"},
            )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_state_code_format(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test country code format validation"""
        mock_call_openweather_api.return_value = sample_geocoding_response

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
                    GET_GEO_BY_LOCATION,
                    {"city": "London", "state_code": code, "country_code": "UK"},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_country_code_format(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test country code format validation"""
        mock_call_openweather_api.return_value = sample_geocoding_response

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
                    GET_GEO_BY_LOCATION,
                    {"city": "London", "state_code": "UK", "country_code": code},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_language_codes(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test invalid limit format"""
        mock_call_openweather_api.return_value = sample_geocoding_response

        invalid_limits = [-1, 0, 6, 10]

        for limit in invalid_limits:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation (^[a-z]{2}$)
                await mcp.call_tool(
                    GET_GEO_BY_LOCATION,
                    {
                        "city": "New York",
                        "state_code": "NY",
                        "country_code": "US",
                        "limit": limit,
                    },
                )


class TestDirectGeoByCoordinates:
    """Test suite for get_localtion_by_geo function."""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_successful_reverse_geocoding_basic(
        self, mock_call_openweather_api, sample_reverse_geocoding_response
    ):
        """Test successful reverse geocoding with basic parameters."""
        mock_call_openweather_api.return_value = sample_reverse_geocoding_response

        result = await mcp.call_tool(
            GET_LOCATOPN_BY_GEO,
            {"lat": 40.7128, "lon": -74.0060},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_reverse_geocoding_response[0]

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.REVERSE_GEOCODING,
            {"lat": 40.7128, "lon": -74.0060, "limit": 5},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_reverse_geocoding_with_custom_limit(
        self, mock_call_openweather_api, sample_reverse_geocoding_response
    ):
        """Test reverse geocoding with custom limit."""
        mock_call_openweather_api.return_value = sample_reverse_geocoding_response

        result = await mcp.call_tool(
            GET_LOCATOPN_BY_GEO,
            {"lat": 40.7128, "lon": -74.0060, "limit": 1},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_reverse_geocoding_response[0]

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.REVERSE_GEOCODING,
            {"lat": 40.7128, "lon": -74.0060, "limit": 1},
            mcp_ctx=ANY,
        )

    @pytest.mark.parametrize(
        "lat,lon",
        [
            (40.7128, -74.0060),
            (51.5074, -0.1278),
            (35.6762, 139.6503),
            (-33.8688, 151.2093),
            (0.0, 0.0),
            (90.0, 0.0),
            (-90.0, 0.0),
            (0.0, 180.0),
            (0.0, -180.0),
        ],
    )
    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_reverse_geocoding_coordinate_ranges(
        self,
        mock_call_openweather_api,
        sample_reverse_geocoding_response,
        lat,
        lon,
    ):
        """Test reverse geocoding with various coordinate ranges."""
        mock_call_openweather_api.return_value = sample_reverse_geocoding_response

        result = await mcp.call_tool(
            GET_LOCATOPN_BY_GEO,
            {"lat": lat, "lon": lon},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_reverse_geocoding_response[0]

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.REVERSE_GEOCODING,
            {"lat": lat, "lon": lon, "limit": 5},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_reverse_geocoding_high_precision_coordinates(
        self, mock_call_openweather_api, sample_reverse_geocoding_response
    ):
        """Test reverse geocoding with high precision coordinates."""
        mock_call_openweather_api.return_value = sample_reverse_geocoding_response

        high_precision_lat = 40.712827449
        high_precision_lon = -74.006015234

        result = await mcp.call_tool(
            GET_LOCATOPN_BY_GEO,
            {"lat": high_precision_lat, "lon": high_precision_lon},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_reverse_geocoding_response[0]

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.REVERSE_GEOCODING,
            {"lat": high_precision_lat, "lon": high_precision_lon, "limit": 5},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
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
                    GET_LOCATOPN_BY_GEO,
                    {"lat": lat, "lon": 0.0},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
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
                    GET_LOCATOPN_BY_GEO,
                    {"lat": 0.0, "lon": lon},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.geocoding.call_openweather_api")
    async def test_invalid_language_codes(
        self, mock_call_openweather_api, sample_geocoding_response
    ):
        """Test invalid limit format"""
        mock_call_openweather_api.return_value = sample_geocoding_response

        invalid_limits = [-1, 0, 6, 10]

        for limit in invalid_limits:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation (^[a-z]{2}$)
                await mcp.call_tool(
                    GET_LOCATOPN_BY_GEO,
                    {"lat": 40.7128, "lon": -74.0060, "limit": limit},
                )
