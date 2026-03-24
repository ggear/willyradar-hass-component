"""Fixtures for WillyWeather Radar tests."""

from __future__ import annotations

import pytest

from homeassistant.loader import DATA_CUSTOM_COMPONENTS

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def _clear_custom_components_cache(hass):
    """Ensure custom components are rediscovered for each test."""
    hass.data.pop(DATA_CUSTOM_COMPONENTS, None)

# Minimal valid 1x1 transparent PNG used across tests.
MOCK_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

MOCK_PROVIDERS_RESPONSE = [
    {
        "overlayPath": "https://cdn.willyweather.com.au/radar/",
        "bounds": {
            "minLat": -44.0,
            "minLng": 112.0,
            "maxLat": -10.0,
            "maxLng": 154.0,
        },
        "overlays": [
            {"dateTime": "2025-01-01 12:00:00", "name": "radar_001.png"},
            {"dateTime": "2025-01-01 12:06:00", "name": "radar_002.png"},
        ],
    }
]


@pytest.fixture
def mock_willyweather_config() -> dict:
    """Return a minimal valid YAML configuration."""
    return {
        "willyradar": {"api_key": "test_key_12345"},
        "camera": [
            {
                "platform": "willyradar",
                "name": "Test Radar",
                "latitude": -33.8688,
                "longitude": 151.2093,
            }
        ],
    }


@pytest.fixture
def mock_willyweather_config_with_processing() -> dict:
    """Return YAML configuration with image processing enabled."""
    return {
        "willyradar": {"api_key": "test_key_12345"},
        "camera": [
            {
                "platform": "willyradar",
                "name": "Processed Radar",
                "latitude": -33.8688,
                "longitude": 151.2093,
                "upscale": True,
                "smooth": True,
                "scale_factor": 2.0,
                "blur_radius": 1.5,
            }
        ],
    }
