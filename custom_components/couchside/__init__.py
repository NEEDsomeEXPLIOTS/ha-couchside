"""Home Assistant integration for Couchside gaming box remote control."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import CouchsideCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Couchside integration (YAML configuration not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Couchside config entry.
    
    Creates the coordinator, refreshes initial data, and forwards setup to all
    platforms (sensor, button, media_player).
    """
    coordinator = CouchsideCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Couchside config entry.
    
    Removes the coordinator and all associated entities.
    """
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
