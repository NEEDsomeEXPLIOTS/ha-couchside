"""Config flow for Couchside: discovers boxes via UDP, validates token via HTTP."""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DEFAULT_PORT, DISCOVERY_MAGIC, DOMAIN
from .coordinator import CouchsideCoordinator


class CouchsideConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Couchside."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input: ConfigType | None = None):
        """Start config or manual entry."""
        errors = {}

        if user_input:
            # Validate manual entry
            try:
                self._discovered_host = cv.string(user_input[CONF_HOST])
                self._discovered_port = int(user_input[CONF_PORT])
                
                # Check if already configured
                await self.async_set_unique_id(
                    f"{self._discovered_host}:{self._discovered_port}"
                )
                self._abort_if_unique_id_configured()
                
                return await self.async_step_token()
            except vol.Invalid:
                errors["base"] = "invalid_host"

        # Try automatic discovery first
        discovered_devices = await self._discover()
        
        if discovered_devices:
            # Show first discovered device, but allow choosing others
            self._discovered_host = discovered_devices[0][CONF_HOST]
            self._discovered_port = discovered_devices[0][CONF_PORT]
            return await self.async_step_token()

        # No discovery - fall back to manual form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, description={
                    "suggested_value": self._discovered_host
                }): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT, description={
                    "suggested_value": self._discovered_port
                }): int,
            }),
            errors=errors,
            description_placeholders={
                "doc_url": "https://github.com/NEEDsomeEXPLIOTS/ha-couchside#setup"
            },
        )

    async def async_step_token(self, user_input: ConfigType | None = None):
        """Validate the bearer token against /api/status."""
        errors = {}

        if user_input:
            token = str(user_input[CONF_TOKEN]).strip()
            
            if not token:
                errors["base"] = "token_required"
            else:
                session = async_get_clientsession(self.hass)
                try:
                    # Test connection with token
                    async with session.get(
                        f"http://{self._discovered_host}:{self._discovered_port}/api/status",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5,
                    ) as response:
                        if response.status == 401:
                            errors["base"] = "invalid_token"
                        elif response.status != 200:
                            errors["base"] = "cannot_connect"
                        else:
                            # Success! Create the entry
                            await self.async_set_unique_id(
                                f"{self._discovered_host}:{self._discovered_port}"
                            )
                            
                            # Abort if already configured (shouldn't happen after abort_if_unique_id_configured above)
                            self._abort_if_unique_id_configured()
                            
                            # Get device info for title
                            data = await response.json()
                            title = data.get("status", {}).get("hostname", "Couchside")
                            
                            return self.async_create_entry(
                                title=title,
                                data={
                                    CONF_HOST: self._discovered_host,
                                    CONF_PORT: self._discovered_port,
                                    CONF_TOKEN: token,
                                },
                            )
                except asyncio.TimeoutError:
                    errors["base"] = "timeout"
                except (OSError, HomeAssistantError):
                    errors["base"] = "cannot_connect"

        # Show token entry form
        return self.async_show_form(
            step_id="token",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN, description={
                    "suggested_value": ""  # Empty by default for security
                }): str,
            }),
            errors=errors,
            description_placeholders={
                "host": self._discovered_host,
                "port": self._discovered_port,
            },
        )

    async def async_step_reauth(self, user_input: ConfigType | None = None):
        """Handle reauth flow when token is rejected."""
        self._reauth_entry = self.hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN, self.context["unique_id"]
        )
        return await self.async_step_token()

    async def _discover(self) -> list[dict[str, Any]]:
        """Broadcast the Couchside UDP discovery packet and wait for replies."""
        loop = asyncio.get_running_loop()
        found: list[dict[str, Any]] = []
        
        # Use a future to signal completion
        discovery_complete = loop.create_future()
        
        class DiscoveryProtocol(asyncio.DatagramProtocol):
            def __init__(self, found_list: list[dict[str, Any]], done_future):
                self.found = found_list
                self.done = done_future
            
            def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
                try:
                    payload = json.loads(data.decode("utf-8"))
                    if payload.get("couchside") is True:
                        item = {
                            CONF_HOST: addr[0],
                            CONF_PORT: int(payload.get("port", DEFAULT_PORT)),
                        }
                        if item not in self.found:
                            self.found.append(item)
                except (ValueError, TypeError, json.JSONDecodeError, KeyError):
                    pass
            
            def connection_lost(self, exc: Exception | None) -> None:
                if not self.done.done():
                    self.done.set_result(None)

        transport = None
        try:
            transport, _ = await loop.create_datagram_endpoint(
                lambda: DiscoveryProtocol(found, discovery_complete),
                local_addr=("0.0.0.0", 0),
                allow_broadcast=True,
            )
            
            # Send discovery packet to broadcast address
            transport.sendto(DISCOVERY_MAGIC, ("255.255.255.255", DEFAULT_PORT))
            
            # Wait for responses (with timeout)
            await asyncio.wait_for(discovery_complete, timeout=2.5)
        except asyncio.TimeoutError:
            # Timeout is okay - just return what we found
            pass
        except OSError:
            # Network error - continue with empty results
            pass
        finally:
            if transport:
                transport.close()
        
        return found


class CouchsideOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for reconfiguration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: ConfigType | None = None):
        """Manage the options."""
        errors = {}

        if user_input:
            new_host = str(user_input[CONF_HOST]).strip()
            new_port = int(user_input[CONF_PORT])
            new_token = str(user_input[CONF_TOKEN]).strip()
            
            # Validate the new settings
            session = async_get_clientsession(self.hass)
            try:
                async with session.get(
                    f"http://{new_host}:{new_port}/api/status",
                    headers={"Authorization": f"Bearer {new_token}"},
                    timeout=5,
                ) as response:
                    if response.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        # Update the entry
                        self.hass.config_entries.async_update_entry(
                            self.config_entry,
                            data={
                                CONF_HOST: new_host,
                                CONF_PORT: new_port,
                                CONF_TOKEN: new_token,
                            },
                        )
                        # Reload the entry
                        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                        return self.async_create_entry(title="", data={})
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except (OSError, HomeAssistantError):
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_HOST,
                    default=self.config_entry.data[CONF_HOST]
                ): str,
                vol.Required(
                    CONF_PORT,
                    default=self.config_entry.data[CONF_PORT]
                ): int,
                vol.Required(
                    CONF_TOKEN,
                    default=self.config_entry.data[CONF_TOKEN]
                ): str,
            }),
            errors=errors,
            description_placeholders={
                "title": self.config_entry.title
            },
        )


@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> CouchsideOptionsFlowHandler:
    """Get the options flow for this handler."""
    return CouchsideOptionsFlowHandler(config_entry)