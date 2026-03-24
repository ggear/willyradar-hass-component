"""Async WillyWeather API client."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class WillyWeatherAPI:
    """Async interface to the WillyWeather API."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialise the API client."""
        self._session = session
        self._api_key = api_key

    async def get_map_providers(
        self,
        lat: float,
        lng: float,
        map_type: str = "radar",
        offset: int = -60,
        limit: int = 60,
    ) -> list[dict[str, Any]]:
        """Get map providers for a location.

        The WillyWeather API expects the request payload in an x-payload
        header rather than in the request body.
        """
        url = f"{API_BASE_URL}/{self._api_key}/maps.json"

        headers = {
            "Content-Type": "application/json",
            "x-payload": json.dumps(
                {
                    "lat": lat,
                    "lng": lng,
                    "mapTypes": [{"code": map_type}],
                    "offset": offset,
                    "limit": limit,
                    "verbose": True,
                    "units": {"distance": "km", "speed": "km/h"},
                }
            ),
        }

        try:
            async with self._session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                data: list[dict[str, Any]] = await resp.json()
                _LOGGER.debug("Received %d providers for %s", len(data), map_type)
                return data
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Failed to get map providers: %s", err)
            return []

    async def download_overlay(
        self, overlay_path: str, overlay_name: str
    ) -> bytes | None:
        """Download a radar overlay image.

        overlay_path may start with '//' or 'https:'.
        """
        if overlay_path.startswith("//"):
            url = f"https:{overlay_path}{overlay_name}"
        elif overlay_path.startswith("https:"):
            url = f"{overlay_path}{overlay_name}"
        else:
            url = overlay_path + overlay_name

        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                data = await resp.read()
                _LOGGER.debug("Downloaded overlay %s (%d bytes)", overlay_name, len(data))
                return data
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Failed to download overlay %s: %s", url, err)
            return None

    async def validate_api_key(self) -> bool:
        """Validate the API key by making a minimal request."""
        providers = await self.get_map_providers(-33.8688, 151.2093, "radar")
        return len(providers) > 0
