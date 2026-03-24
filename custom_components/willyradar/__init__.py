"""WillyWeather Radar integration for Home Assistant."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WillyWeather Radar component from YAML."""
    if DOMAIN not in config:
        return True

    hass.data[DOMAIN] = {
        CONF_API_KEY: config[DOMAIN][CONF_API_KEY],
    }

    _LOGGER.debug("WillyWeather Radar domain configured")
    return True
