"""Tests for WillyWeather Radar camera platform."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.willyradar.const import (
    ATTR_BOUNDS_EAST,
    ATTR_BOUNDS_NORTH,
    ATTR_BOUNDS_SOUTH,
    ATTR_BOUNDS_WEST,
    DOMAIN,
)

from .conftest import MOCK_PNG_BYTES, MOCK_PROVIDERS_RESPONSE


async def _setup_camera(
    hass: HomeAssistant, aioclient_mock, config: dict
) -> None:
    """Set up domain and camera platform with mocked API responses."""
    aioclient_mock.get(
        "https://api.willyweather.com.au/v2/test_key_12345/maps.json",
        json=MOCK_PROVIDERS_RESPONSE,
    )
    aioclient_mock.get(
        "https://cdn.willyweather.com.au/radar/radar_002.png",
        content=MOCK_PNG_BYTES,
    )

    assert await async_setup_component(hass, DOMAIN, config)
    assert await async_setup_component(hass, "camera", config)
    await hass.async_block_till_done()


async def test_camera_setup(
    hass: HomeAssistant, aioclient_mock, mock_willyweather_config: dict
) -> None:
    """Test camera entity is created from YAML config."""
    await _setup_camera(hass, aioclient_mock, mock_willyweather_config)

    state = hass.states.get("camera.test_radar")
    assert state is not None


async def test_camera_image_returns_bytes(
    hass: HomeAssistant, aioclient_mock, mock_willyweather_config: dict
) -> None:
    """Test async_camera_image returns PNG bytes."""
    await _setup_camera(hass, aioclient_mock, mock_willyweather_config)

    camera = hass.data["camera"].get_entity("camera.test_radar")
    assert camera is not None

    image = await camera.async_camera_image()
    assert image is not None
    assert image[:4] == b"\x89PNG"


async def test_camera_extra_state_attributes(
    hass: HomeAssistant, aioclient_mock, mock_willyweather_config: dict
) -> None:
    """Test bounds are exposed as state attributes after fetching an image."""
    await _setup_camera(hass, aioclient_mock, mock_willyweather_config)

    camera = hass.data["camera"].get_entity("camera.test_radar")
    assert camera is not None

    # Bounds are only populated after the first image fetch (on-demand)
    await camera.async_camera_image()
    await hass.async_block_till_done()

    # Force state write so attributes reflect the updated bounds
    camera.async_write_ha_state()
    await hass.async_block_till_done()

    state = hass.states.get("camera.test_radar")
    assert state is not None
    attrs = state.attributes
    assert attrs.get(ATTR_BOUNDS_SOUTH) == -44.0
    assert attrs.get(ATTR_BOUNDS_WEST) == 112.0
    assert attrs.get(ATTR_BOUNDS_NORTH) == -10.0
    assert attrs.get(ATTR_BOUNDS_EAST) == 154.0


async def test_camera_uses_ha_coordinates_fallback(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """Test camera falls back to HA config coordinates when not specified."""
    hass.config.latitude = -37.8136
    hass.config.longitude = 144.9631

    config = {
        "willyradar": {"api_key": "test_key_12345"},
        "camera": [
            {
                "platform": "willyradar",
                "name": "Melbourne Radar",
            }
        ],
    }

    aioclient_mock.get(
        "https://api.willyweather.com.au/v2/test_key_12345/maps.json",
        json=MOCK_PROVIDERS_RESPONSE,
    )
    aioclient_mock.get(
        "https://cdn.willyweather.com.au/radar/radar_002.png",
        content=MOCK_PNG_BYTES,
    )

    assert await async_setup_component(hass, DOMAIN, config)
    assert await async_setup_component(hass, "camera", config)
    await hass.async_block_till_done()

    state = hass.states.get("camera.melbourne_radar")
    assert state is not None


async def test_camera_caches_same_overlay(
    hass: HomeAssistant, aioclient_mock, mock_willyweather_config: dict
) -> None:
    """Test that requesting the same overlay twice only downloads once."""
    await _setup_camera(hass, aioclient_mock, mock_willyweather_config)

    camera = hass.data["camera"].get_entity("camera.test_radar")

    # First call downloads the image
    image1 = await camera.async_camera_image()
    assert image1 is not None

    # Mock a second metadata call (same overlay name returned)
    aioclient_mock.get(
        "https://api.willyweather.com.au/v2/test_key_12345/maps.json",
        json=MOCK_PROVIDERS_RESPONSE,
    )

    # Second call should use cached image (no new overlay download)
    image2 = await camera.async_camera_image()
    assert image2 is image1  # same object, not just equal


async def test_camera_api_failure_returns_cached(
    hass: HomeAssistant, aioclient_mock, mock_willyweather_config: dict
) -> None:
    """Test that API failure returns the previously cached image."""
    await _setup_camera(hass, aioclient_mock, mock_willyweather_config)

    camera = hass.data["camera"].get_entity("camera.test_radar")
    image1 = await camera.async_camera_image()
    assert image1 is not None

    # Next metadata call fails
    aioclient_mock.get(
        "https://api.willyweather.com.au/v2/test_key_12345/maps.json",
        status=500,
    )

    image2 = await camera.async_camera_image()
    assert image2 is image1  # returns cached


async def test_camera_no_domain_config_logs_error(
    hass: HomeAssistant, aioclient_mock, caplog
) -> None:
    """Test camera platform fails gracefully without domain config."""
    config = {
        "camera": [
            {
                "platform": "willyradar",
                "name": "No Domain",
            }
        ],
    }

    assert await async_setup_component(hass, "camera", config)
    await hass.async_block_till_done()

    assert "domain not configured" in caplog.text.lower()


async def test_camera_with_processing(
    hass: HomeAssistant,
    aioclient_mock,
    mock_willyweather_config_with_processing: dict,
) -> None:
    """Test camera applies image processing when configured."""
    await _setup_camera(
        hass, aioclient_mock, mock_willyweather_config_with_processing
    )

    camera = hass.data["camera"].get_entity("camera.processed_radar")
    assert camera is not None

    image = await camera.async_camera_image()
    assert image is not None
    assert image[:4] == b"\x89PNG"


async def test_camera_processing_disabled_returns_raw(
    hass: HomeAssistant, aioclient_mock, mock_willyweather_config: dict
) -> None:
    """Test camera returns raw image when processing is disabled."""
    await _setup_camera(hass, aioclient_mock, mock_willyweather_config)

    camera = hass.data["camera"].get_entity("camera.test_radar")
    image = await camera.async_camera_image()

    # With processing disabled, result should be the raw MOCK_PNG_BYTES
    assert image == MOCK_PNG_BYTES
