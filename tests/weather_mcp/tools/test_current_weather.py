import json
from unittest.mock import ANY, patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import TextContent

from enums.openweather import OpenWeatherEndpoint
from weather_mcp.server import mcp

GET_CURRENT_WEATHER_BY_GEO = "get_current_weather_by_geo"
GET_CURRENT_WEATHER_BY_CITY = "get_current_weather_by_city"


class TestCurrentWeatherToolsRregistration:
    """Test suite for current weather tools registration"""

    @pytest.mark.asyncio
    async def test_current_weather_tools_registration(self):
        import weather_mcp.tools  # noqa: F401

        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert GET_CURRENT_WEATHER_BY_GEO in tool_names
        assert GET_CURRENT_WEATHER_BY_CITY in tool_names


class TestGetCurrentWeatherByGeo:
    """Test suite for get_current_weather_by_geo function"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_valid_coordinates_success(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test successful weather retrieval with valid coordinates"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_GEO,
            {"lat": 35.6762, "lon": 139.6503},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_WEATHER,
            {"lat": 35.6762, "lon": 139.6503, "lang": "en"},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_custom_language_parameter(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test weather retrieval with custom language"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_GEO,
            {"lat": 48.8566, "lon": 2.3522, "lang": "fr"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_WEATHER,
            {"lat": 48.8566, "lon": 2.3522, "lang": "fr"},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_boundary_coordinates(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test with boundary coordinate values"""
        mock_call_openweather_api.return_value = sample_weather_response

        # Test northern boundary
        await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_GEO,
            {"lat": 90.0, "lon": 0.0},
        )

        # Test southern boundary
        await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_GEO,
            {"lat": -90.0, "lon": 0.0},
        )

        # Test eastern boundary
        await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_GEO,
            {"lat": 0.0, "lon": 180.0},
        )

        # Test western boundary
        await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_GEO,
            {"lat": 0.0, "lon": -180.0},
        )

        assert mock_call_openweather_api.call_count == 4

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_high_precision_coordinates(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test with high precision coordinates"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_GEO, {"lat": 35.676234567, "lon": 139.650345678}
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_WEATHER,
            {"lat": 35.676234567, "lon": 139.650345678, "lang": "en"},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
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
                    GET_CURRENT_WEATHER_BY_GEO,
                    {"lat": lat, "lon": 0.0},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
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
                    GET_CURRENT_WEATHER_BY_GEO,
                    {"lat": 0.0, "lon": lon},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_invalid_language_codes(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test invalid language code format"""
        mock_call_openweather_api.return_value = sample_weather_response

        invalid_langs = ["eng", "E", "123", "en-US", "EN"]

        for lang in invalid_langs:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation (^[a-z]{2}$)
                await mcp.call_tool(
                    GET_CURRENT_WEATHER_BY_GEO,
                    {"lat": 35.6762, "lon": 139.6503, "lang": lang},
                )


class TestGetCurrentWeatherByCity:
    """Test suite for get_current_weather_by_city function"""

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_city_only_success(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test successful weather retrieval with city name only"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_CITY,
            {"city": "Tokyo"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_WEATHER,
            {"q": "Tokyo", "lang": "en"},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_city_with_country_code(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test weather retrieval with city and country code"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_CITY,
            {"city": "London", "country_code": "GB"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_WEATHER,
            {"q": "London,GB", "lang": "en"},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_city_with_custom_language(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test weather retrieval with custom language"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_CITY,
            {"city": "París", "country_code": "FR", "lang": "es"},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_WEATHER,
            {"q": "París,FR", "lang": "es"},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_unicode_city_names(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test with Unicode city names"""
        mock_call_openweather_api.return_value = sample_weather_response

        unicode_cities = [
            ("東京", "JP"),
            ("北京", "CN"),
            ("São Paulo", "BR"),
            ("Москва", "RU"),
            ("القاهرة", "EG"),
        ]

        for city, country in unicode_cities:
            result = await mcp.call_tool(
                GET_CURRENT_WEATHER_BY_CITY,
                {"city": city, "country_code": country},
            )

            assert isinstance(result[0], TextContent)
            assert json.loads(result[0].text) == sample_weather_response

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_city_name_trimming(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test that city names are properly trimmed"""
        mock_call_openweather_api.return_value = sample_weather_response

        result = await mcp.call_tool(
            GET_CURRENT_WEATHER_BY_CITY,
            {"city": "  Tokyo  "},
        )

        assert isinstance(result[0], TextContent)
        assert json.loads(result[0].text) == sample_weather_response

        mock_call_openweather_api.assert_called_once_with(
            OpenWeatherEndpoint.CURRENT_WEATHER,
            {"q": "Tokyo", "lang": "en"},
            mcp_ctx=ANY,
        )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_empty_city_name_handling(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test handling of empty city name"""
        mock_call_openweather_api.return_value = sample_weather_response

        # This should be caught by Pydantic min_length=1 validation
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_CURRENT_WEATHER_BY_CITY,
                {"city": ""},
            )

        # Test with whitespace-only string
        with pytest.raises(ToolError):
            await mcp.call_tool(
                GET_CURRENT_WEATHER_BY_CITY,
                {"city": "   "},
            )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_invalid_country_code_format(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test country code format validation"""
        mock_call_openweather_api.return_value = sample_weather_response

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
                    GET_CURRENT_WEATHER_BY_CITY,
                    {"city": "London", "country_code": code},
                )

    @pytest.mark.asyncio
    @patch("weather_mcp.tools.current_weather.call_openweather_api")
    async def test_invalid_language_codes(
        self, mock_call_openweather_api, sample_weather_response
    ):
        """Test invalid language code format"""
        mock_call_openweather_api.return_value = sample_weather_response

        invalid_langs = ["eng", "E", "123", "en-US", "EN"]

        for lang in invalid_langs:
            with pytest.raises(ToolError):
                # This should raise ValidationError due to Pydantic pattern validation (^[a-z]{2}$)
                await mcp.call_tool(
                    GET_CURRENT_WEATHER_BY_CITY,
                    {"city": "Tokyo", "lang": lang},
                )
