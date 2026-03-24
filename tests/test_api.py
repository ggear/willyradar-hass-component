"""Tests for WillyWeather API client."""

from __future__ import annotations

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.willyradar.api import WillyWeatherAPI
from custom_components.willyradar.const import API_BASE_URL

from .conftest import MOCK_PNG_BYTES, MOCK_PROVIDERS_RESPONSE


async def test_get_map_providers(hass: HomeAssistant, aioclient_mock) -> None:
    """Test fetching map providers returns parsed JSON."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "test_key")

    aioclient_mock.get(
        f"{API_BASE_URL}/test_key/maps.json",
        json=MOCK_PROVIDERS_RESPONSE,
    )

    result = await api.get_map_providers(-33.87, 151.21, "radar")
    assert len(result) == 1
    assert result[0]["overlays"][0]["name"] == "radar_001.png"
    assert result[0]["bounds"]["minLat"] == -44.0


async def test_get_map_providers_sends_x_payload_header(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test that the x-payload header is sent with the correct structure."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "test_key")

    aioclient_mock.get(
        f"{API_BASE_URL}/test_key/maps.json",
        json=[],
    )

    await api.get_map_providers(-33.87, 151.21, "radar", offset=-30, limit=30)

    assert aioclient_mock.call_count == 1
    call = aioclient_mock.mock_calls[0]
    headers = call[3]  # (method, url, data, headers)
    assert "x-payload" in headers

    import json

    payload = json.loads(headers["x-payload"])
    assert payload["lat"] == -33.87
    assert payload["lng"] == 151.21
    assert payload["mapTypes"] == [{"code": "radar"}]
    assert payload["offset"] == -30
    assert payload["limit"] == 30


async def test_get_map_providers_http_error(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test API returns empty list on HTTP error."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "test_key")

    aioclient_mock.get(
        f"{API_BASE_URL}/test_key/maps.json",
        status=500,
    )

    result = await api.get_map_providers(-33.87, 151.21, "radar")
    assert result == []


async def test_get_map_providers_connection_error(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test API returns empty list on connection error."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "test_key")

    aioclient_mock.get(
        f"{API_BASE_URL}/test_key/maps.json",
        exc=aiohttp.ClientConnectionError(),
    )

    result = await api.get_map_providers(-33.87, 151.21, "radar")
    assert result == []


async def test_download_overlay(hass: HomeAssistant, aioclient_mock) -> None:
    """Test downloading overlay returns bytes."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "test_key")

    aioclient_mock.get(
        "https://cdn.willyweather.com.au/radar/radar_001.png",
        content=MOCK_PNG_BYTES,
    )

    result = await api.download_overlay(
        "https://cdn.willyweather.com.au/radar/", "radar_001.png"
    )
    assert result == MOCK_PNG_BYTES


async def test_download_overlay_protocol_relative(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test overlay path starting with // gets https: prepended."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "test_key")

    aioclient_mock.get(
        "https://cdn.willyweather.com.au/radar/radar_001.png",
        content=MOCK_PNG_BYTES,
    )

    result = await api.download_overlay(
        "//cdn.willyweather.com.au/radar/", "radar_001.png"
    )
    assert result == MOCK_PNG_BYTES


async def test_download_overlay_failure(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test download returns None on failure."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "test_key")

    aioclient_mock.get(
        "https://cdn.willyweather.com.au/radar/bad.png",
        status=404,
    )

    result = await api.download_overlay(
        "https://cdn.willyweather.com.au/radar/", "bad.png"
    )
    assert result is None


async def test_validate_api_key_success(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test API key validation succeeds with valid response."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "good_key")

    aioclient_mock.get(
        f"{API_BASE_URL}/good_key/maps.json",
        json=MOCK_PROVIDERS_RESPONSE,
    )

    assert await api.validate_api_key() is True


async def test_validate_api_key_failure(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test API key validation fails on 401."""
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, "bad_key")

    aioclient_mock.get(
        f"{API_BASE_URL}/bad_key/maps.json",
        status=401,
    )

    assert await api.validate_api_key() is False
