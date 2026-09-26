"""Home Assistant integration for Couchside gaming box remote control."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, CONF_ENABLE_NOTIFICATIONS
from .coordinator import CouchsideCoordinator
from .services import async_send_alert

# Store the unload handle for cleanup
UNLOAD_LISTENERS: dict[str, callable] = {}


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Couchside integration."""
    # Set up notification listeners for each entry
    async def setup_alert_listener(entry: ConfigEntry):
        """Set up alert listener when thermal/battery conditions change."""
        if not entry.options.get(CONF_ENABLE_NOTIFICATIONS, True):
            return
        
        # This would be implemented with event listeners in a real integration
        _LOGGER.debug("Alert listener registered for %s", entry.entry_id)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry and forward it to all platforms."""
    coordinator = CouchsideCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    # Forward to all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register alert listener
    UNLOAD_LISTENERS[entry.entry_id] = True  # Placeholder for real listener
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and remove stored coordinator data."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        UNLOAD_LISTENERS.pop(entry.entry_id, None)
    return unloaded