"""Config flow: discover Couchside over its UDP probe, then request the token."""
from __future__ import annotations

import asyncio
import json
import socket
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DEFAULT_PORT, DISCOVERY_MAGIC, DOMAIN


class CouchsideConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input:
            self._discovered = {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            return await self.async_step_token()
        devices = await self._discover()
        if not devices:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({
                vol.Required(CONF_HOST): str, vol.Required(CONF_PORT, default=DEFAULT_PORT): int}))
        self._discovered = devices[0]
        return await self.async_step_token()

    async def async_step_token(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input:
            token = user_input[CONF_TOKEN].strip()
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{self._discovered[CONF_HOST]}:{self._discovered[CONF_PORT]}/api/status",
                        headers={"Authorization": f"Bearer {token}"}, timeout=5) as response:
                        if response.status != 200:
                            raise ValueError
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{self._discovered[CONF_HOST]}:{self._discovered[CONF_PORT]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Couchside", data={**self._discovered, CONF_TOKEN: token})
        return self.async_show_form(step_id="token", data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}), errors=errors)

    async def _discover(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        found: list[dict[str, Any]] = []
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: _DiscoveryProtocol(found), local_addr=("0.0.0.0", 0), allow_broadcast=True)
        try:
            transport.sendto(DISCOVERY_MAGIC, ("255.255.255.255", DEFAULT_PORT))
            await asyncio.sleep(1.5)
        finally:
            transport.close()
        return found


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, found: list[dict[str, Any]]) -> None:
        self.found = found
    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            payload = json.loads(data)
            if payload.get("couchside") is True:
                item = {CONF_HOST: addr[0], CONF_PORT: int(payload.get("port", DEFAULT_PORT))}
                if item not in self.found:
                    self.found.append(item)
        except (ValueError, TypeError, json.JSONDecodeError):
            return
