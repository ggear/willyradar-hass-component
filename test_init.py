"""Tests for WillyWeather Radar domain setup."""

from __future__ import annotations

import pytest
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.willyradar.const import DOMAIN


async def test_async_setup_success(
    hass: HomeAssistant, mock_willyweather_config: dict
) -> None:
    """Test successful domain setup stores api_key in hass.data."""
    result = await async_setup_component(hass, DOMAIN, mock_willyweather_config)
    assert result is True
    assert DOMAIN in hass.data
    assert hass.data[DOMAIN]["api_key"] == "test_key_12345"


async def test_async_setup_no_config(hass: HomeAssistant) -> None:
    """Test setup returns True when domain is not in config."""
    result = await async_setup_component(hass, DOMAIN, {})
    assert result is True
    assert DOMAIN not in hass.data


async def test_async_setup_missing_api_key(hass: HomeAssistant) -> None:
    """Test schema rejects missing api_key."""
    from custom_components.willyradar import CONFIG_SCHEMA

    with pytest.raises(vol.MultipleInvalid):
        CONFIG_SCHEMA({DOMAIN: {}})


async def test_async_setup_empty_api_key(hass: HomeAssistant) -> None:
    """Test schema rejects None api_key."""
    from custom_components.willyradar import CONFIG_SCHEMA

    with pytest.raises(vol.MultipleInvalid):
        CONFIG_SCHEMA({DOMAIN: {"api_key": None}})
