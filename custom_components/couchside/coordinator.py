"""Couchside API coordinator with data refresh and action execution."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CouchsideCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate data updates from the Couchside agent.
    
    Polls /api/status, /api/actions, /api/media, and /api/tv every 30 seconds.
    Gracefully handles optional endpoints (e.g., /api/tv returns 404 if no TV backend).
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self._http = async_get_clientsession(hass)
        self.base = f"http://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))

    async def _get(self, path: str, optional: bool = False) -> Any:
        """Fetch a single endpoint from the Couchside agent.
        
        Args:
            path: API endpoint path (e.g., "/api/status")
            optional: if True, return {} on 404; else raise UpdateFailed
            
        Returns:
            Parsed JSON response or {} if optional and 404.
            
        Raises:
            UpdateFailed: on auth failure, network error, or non-404 HTTP error.
        """
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.get(
            self.base + path, headers=headers, timeout=10
        ) as response:
            if response.status == 401:
                raise UpdateFailed("Couchside token rejected")
            if response.status == 404 and optional:
                return {}  # Graceful fallback for optional endpoints
            if response.status >= 400:
                raise UpdateFailed(f"Couchside returned HTTP {response.status}")
            return await response.json()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and merge all coordinator data sources.
        
        Treats /api/tv as optional (returns {} on 404) because a box without
        a TV backend will not serve that endpoint.
        
        Returns:
            Dict with keys: status, actions, media, tv
            
        Raises:
            UpdateFailed: if any required endpoint fails or on network error.
        """
        try:
            # Fetch required endpoints in parallel
            status, actions, media = await asyncio.gather(
                self._get("/api/status"),
                self._get("/api/actions"),
                self._get("/api/media"),
            )
            # /api/tv is optional (boxes without TV backend return 404)
            tv = await self._get("/api/tv", optional=True)
            
            return {"status": status, "actions": actions, "media": media, "tv": tv}
        except (ClientError, TimeoutError, UpdateFailed) as err:
            raise UpdateFailed(str(err)) from err

    async def async_action(self, action_id: str) -> dict[str, Any]:
        """Execute a configured Couchside action.
        
        Args:
            action_id: action ID from /api/actions (allowlisted by the agent)
            
        Returns:
            Result dict with keys: ok, exit_code, stdout, stderr, duration_ms
            
        Raises:
            UpdateFailed: on HTTP error or network failure.
        """
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.post(
            self.base + "/api/actions/" + action_id,
            headers=headers,
            timeout=30,
        ) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Action failed: HTTP {response.status}")
            return await response.json()

    async def async_media_command(
        self, player: str, operation: str, body: dict | None = None
    ) -> None:
        """Send a media player command (play, pause, seek, etc.).
        
        Args:
            player: player ID from /api/media
            operation: one of play, pause, play_pause, next, previous, seek
            body: optional JSON body for operations like seek ({"position_ms": ...})
            
        Raises:
            UpdateFailed: on HTTP error or network failure.
        """
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.post(
            f"{self.base}/api/media/{player}/{operation}",
            headers=headers,
            json=body,
            timeout=10,
        ) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Media command failed: HTTP {response.status}")
        # Refresh coordinator data after action to reflect new state
        await self.async_request_refresh()
