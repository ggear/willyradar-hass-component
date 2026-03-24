"""Camera platform for WillyWeather Radar."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import voluptuous as vol

from homeassistant.components.camera import Camera, PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import WillyWeatherAPI
from .const import (
    ATTR_BOUNDS_EAST,
    ATTR_BOUNDS_NORTH,
    ATTR_BOUNDS_SOUTH,
    ATTR_BOUNDS_WEST,
    CONF_BLUR_RADIUS,
    CONF_SCALE_FACTOR,
    CONF_SMOOTH,
    CONF_UPSCALE,
    DEFAULT_BLUR_RADIUS,
    DEFAULT_SCALE_FACTOR,
    DEFAULT_SMOOTH,
    DEFAULT_UPSCALE,
    DOMAIN,
)
from .image_processing import process_radar_image

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default="willy_radar"): cv.string,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_UPSCALE, default=DEFAULT_UPSCALE): cv.boolean,
        vol.Optional(CONF_SMOOTH, default=DEFAULT_SMOOTH): cv.boolean,
        vol.Optional(CONF_SCALE_FACTOR, default=DEFAULT_SCALE_FACTOR): vol.All(
            vol.Coerce(float), vol.Range(min=1.0, max=3.0)
        ),
        vol.Optional(CONF_BLUR_RADIUS, default=DEFAULT_BLUR_RADIUS): vol.All(
            vol.Coerce(float), vol.Range(min=0.5, max=3.0)
        ),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the WillyWeather Radar camera platform."""
    domain_data = hass.data.get(DOMAIN)
    if domain_data is None:
        _LOGGER.error(
            "WillyWeather Radar domain not configured. "
            "Add 'willyradar:' with api_key to configuration.yaml"
        )
        return

    api_key = domain_data[CONF_API_KEY]
    session = async_get_clientsession(hass)
    api = WillyWeatherAPI(session, api_key)

    lat = config.get(CONF_LATITUDE, hass.config.latitude)
    lng = config.get(CONF_LONGITUDE, hass.config.longitude)
    name = config[CONF_NAME]

    camera = WillyWeatherRadarCamera(
        hass=hass,
        api=api,
        name=name,
        latitude=lat,
        longitude=lng,
        upscale=config[CONF_UPSCALE],
        smooth=config[CONF_SMOOTH],
        scale_factor=config[CONF_SCALE_FACTOR],
        blur_radius=config[CONF_BLUR_RADIUS],
    )

    async_add_entities([camera], update_before_add=True)


class WillyWeatherRadarCamera(Camera):
    """A camera entity that serves WillyWeather radar imagery on demand."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: WillyWeatherAPI,
        name: str,
        latitude: float,
        longitude: float,
        upscale: bool,
        smooth: bool,
        scale_factor: float,
        blur_radius: float,
    ) -> None:
        """Initialise the radar camera."""
        super().__init__()
        self.hass = hass
        self._api = api
        self._attr_name = name
        self._latitude = latitude
        self._longitude = longitude
        self._upscale = upscale
        self._smooth = smooth
        self._scale_factor = scale_factor
        self._blur_radius = blur_radius

        self._lock = asyncio.Lock()
        self._cached_image: bytes | None = None
        self._cached_overlay_name: str | None = None
        self._bounds: dict[str, float] = {}

        # Metadata cache: avoid hitting the API on every image request.
        # WillyWeather radar updates every 6-10 minutes, so 5 min TTL is safe.
        self._metadata_ttl = 300  # seconds
        self._cached_providers: list[dict[str, Any]] | None = None
        self._metadata_fetched_at: float = 0.0

    @property
    def unique_id(self) -> str:
        """Return a unique ID based on coordinates."""
        return f"willyradar_{self._latitude}_{self._longitude}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return radar bounds as state attributes."""
        return {
            ATTR_BOUNDS_SOUTH: self._bounds.get("minLat"),
            ATTR_BOUNDS_WEST: self._bounds.get("minLng"),
            ATTR_BOUNDS_NORTH: self._bounds.get("maxLat"),
            ATTR_BOUNDS_EAST: self._bounds.get("maxLng"),
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Fetch the latest radar image on demand.

        Uses an asyncio.Lock to prevent concurrent API calls when multiple
        clients request the image simultaneously.
        """
        async with self._lock:
            return await self._fetch_radar()

    async def _fetch_radar(self) -> bytes | None:
        """Fetch radar from WillyWeather, applying optional processing."""
        now = time.monotonic()

        # Use cached metadata if within TTL
        if (
            self._cached_providers is not None
            and (now - self._metadata_fetched_at) < self._metadata_ttl
        ):
            providers = self._cached_providers
        else:
            providers = await self._api.get_map_providers(
                self._latitude, self._longitude, "radar"
            )
            if providers:
                self._cached_providers = providers
                self._metadata_fetched_at = now

        if not providers:
            _LOGGER.warning("No radar providers returned")
            return self._cached_image

        provider = providers[0]
        overlays = provider.get("overlays", [])

        if not overlays:
            _LOGGER.warning("No radar overlays available")
            return self._cached_image

        overlay = overlays[-1]
        overlay_name = overlay["name"]

        # Return cached image if the overlay hasn't changed
        if overlay_name == self._cached_overlay_name and self._cached_image:
            _LOGGER.debug("Returning cached image for %s", overlay_name)
            return self._cached_image

        # Download the new overlay
        image_data = await self._api.download_overlay(
            provider["overlayPath"], overlay_name
        )

        if image_data is None:
            _LOGGER.error("Failed to download overlay %s", overlay_name)
            return self._cached_image

        # Apply server-side processing if configured
        if self._upscale or self._smooth:
            try:
                image_data = await self.hass.async_add_executor_job(
                    process_radar_image,
                    image_data,
                    self._upscale,
                    self._smooth,
                    self._scale_factor,
                    self._blur_radius,
                )
            except ImportError:
                _LOGGER.error(
                    "Pillow is required for image processing. "
                    "Install it or disable upscale/smooth in configuration"
                )
            except Exception:
                _LOGGER.exception("Image processing failed, using raw image")

        # Update cache and bounds
        self._cached_image = image_data
        self._cached_overlay_name = overlay_name
        self._bounds = provider.get("bounds", {})

        _LOGGER.debug(
            "Updated radar image: %s (%d bytes)", overlay_name, len(image_data)
        )
        return image_data
