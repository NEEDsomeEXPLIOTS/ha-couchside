"""Couchside API coordinator."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CouchsideCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.session = hass.helpers.network.get_url if False else None
        self.client = None
        self._http = hass.helpers.aiohttp.async_get_clientsession(hass)
        self.base = f"http://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))

    async def _get(self, path: str) -> Any:
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.get(self.base + path, headers=headers, timeout=10) as response:
            if response.status == 401:
                raise UpdateFailed("Couchside token rejected")
            if response.status >= 400:
                raise UpdateFailed(f"Couchside returned HTTP {response.status}")
            return await response.json()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status, actions, media, tv = await __import__("asyncio").gather(
                self._get("/api/status"), self._get("/api/actions"),
                self._get("/api/media"), self._get("/api/tv"))
            return {"status": status, "actions": actions, "media": media, "tv": tv}
        except (ClientError, TimeoutError, UpdateFailed) as err:
            raise UpdateFailed(str(err)) from err

    async def async_action(self, action_id: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.post(self.base + "/api/actions/" + action_id,
                                   headers=headers, timeout=30) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Action failed: HTTP {response.status}")
            return await response.json()

    async def async_media_command(self, player: str, operation: str, body: dict | None = None) -> None:
        headers = {"Authorization": f"Bearer {self.entry.data[CONF_TOKEN]}"}
        async with self._http.post(f"{self.base}/api/media/{player}/{operation}",
                                   headers=headers, json=body, timeout=10) as response:
            if response.status >= 400:
                raise UpdateFailed(f"Media command failed: HTTP {response.status}")
        await self.async_request_refresh()
