"""Couchside API coordinator with TV control methods."""
# At the top, after imports
import time
from collections import deque

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
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._http = async_get_clientsession(hass)
        self.base = f"http://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
        self.response_times: deque[float] = deque(maxlen=100)
        self.poll_count = 0
        self.last_failure_time: datetime | None = None
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))

    async def _get(self, path: str, optional: bool = False) -> Any:
        """Fetch a single endpoint from the Couchside agent."""
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.get(self.base + path, headers=headers, timeout=10) as response:
            if response.status == 401:
                raise UpdateFailed("Couchside token rejected")
            if response.status == 404 and optional:
                return {}
            if response.status >= 400:
                raise UpdateFailed(f"Couchside returned HTTP {response.status}")
            return await response.json()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all required data from the Couchside agent."""
        start_time = time.time()
        self.poll_count += 1
        
        try:
            status, actions, media = await asyncio.gather(
                self._get("/api/status"),
                self._get("/api/actions"),
                self._get("/api/media"),
            )
            tv = await self._get("/api/tv", optional=True)
            
            # Track response time
            elapsed = (time.time() - start_time) * 1000  # ms
            self.response_times.append(elapsed)
            self.last_failure_time = None
            
            return {"status": status, "actions": actions, "media": media, "tv": tv}
            
        except (ClientError, TimeoutError, UpdateFailed) as err:
            self.last_failure_time = datetime.now()
            raise UpdateFailed(str(err)) from err
    
    @property
    def avg_response_ms(self) -> float | None:
        """Calculate average response time in milliseconds."""
        if not self.response_times:
            return None
        return sum(self.response_times) / len(self.response_times)

    @property
    def avg_response_ms(self) -> float | None:
        """Calculate average response time in milliseconds."""
        if not self.response_times:
            return None
        return sum(self.response_times) / len(self.response_times)
    async def async_action(self, action_id: str) -> dict[str, Any]:
        """Execute a configured Couchside action."""
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.post(
            self.base + "/api/actions/" + action_id,
            headers=headers,
            timeout=30,
        ) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Action failed: HTTP {response.status}")
            return await response.json()

    async def async_media_command(self, player: str, operation: str, body: dict | None = None) -> None:
        """Send a media control command to the Couchside box."""
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.post(
            f"{self.base}/api/media/{player}/{operation}",
            headers=headers,
            json=body,
            timeout=10,
        ) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Media command failed: HTTP {response.status}")
        await self.async_request_refresh()

    async def async_tv_command(self, command: str, body: dict | None = None) -> None:
        """Send a TV control command (power, volume, input)."""
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.post(
            f"{self.base}/api/tv/{command}",
            headers=headers,
            json=body,
            timeout=10,
        ) as response:
            if response.status >= 400:
                raise UpdateFailed(f"TV command failed: HTTP {response.status}")
        await self.async_request_refresh()