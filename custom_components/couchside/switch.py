"""Couchside switch entities for feature toggles."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from homeassistant.helpers.update_coordinator import CoordinatorEntity # type: ignore

from .const import CONF_ENABLE_NOTIFICATIONS, DOMAIN # type: ignore
from .coordinator import CouchsideCoordinator # type: ignore

async def async_setup_entry(hass, entry, async_add_entities):
    """Create switch entities for feature toggles."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        NotificationsSwitch(coordinator),
        AutoDiscoverySwitch(coordinator),
    ]
    
    if coordinator.data.get("tv"):
        entities.append(TVPowerSaveSwitch(coordinator))
    
    async_add_entities(entities, update_before_add=True)

def _device_name(status: dict) -> str:
    """Format a polished device name from hostname and OS."""
    hostname = status.get("hostname", "Couchside").title()
    os_name = status.get("os", {}).get("name", "")
    if os_name:
        return f"{hostname} ({os_name})"
    return hostname

class NotificationsSwitch(CoordinatorEntity, SwitchEntity):
    """Enable/disable thermal and battery notifications."""

    def __init__(self, coordinator: CouchsideCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._attr_name = "Enable Notifications"
        self._attr_icon = "mdi:bell-ring"
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        status = self.coordinator.data.get("status", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=_device_name(status),
            manufacturer="EmeryTech",
            model=status.get("os", {}).get("name", "Unknown"),
            hw_version=status.get("os", {}).get("build", "Unknown"),
            sw_version=status.get("agent_version", "Unknown"),
        )

    @property
    def unique_id(self):
        return f"{self.coordinator.entry.entry_id}_notifications"

    @property
    def is_on(self) -> bool:
        """Get notification preference from options."""
        return self.coordinator.entry.options.get(
            CONF_ENABLE_NOTIFICATIONS, True
        )

    async def async_turn_on(self) -> None:
        """Enable notifications."""
        new_options = dict(self.coordinator.entry.options)
        new_options[CONF_ENABLE_NOTIFICATIONS] = True
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )

    async def async_turn_off(self) -> None:
        """Disable notifications."""
        new_options = dict(self.coordinator.entry.options)
        new_options[CONF_ENABLE_NOTIFICATIONS] = False
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )

class AutoDiscoverySwitch(CoordinatorEntity, SwitchEntity):
    """Enable/disable automatic discovery for this entry."""

    def __init__(self, coordinator: CouchsideCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._attr_name = "Auto Discovery"
        self._attr_icon = "mdi:magnify"
        self._attr_has_entity_name = True
        self._key = "auto_discovery_enabled"

    @property
    def device_info(self) -> DeviceInfo:
        status = self.coordinator.data.get("status", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=_device_name(status),
            manufacturer="EmeryTech",
            model=status.get("os", {}).get("name", "Unknown"),
            hw_version=status.get("os", {}).get("build", "Unknown"),
            sw_version=status.get("agent_version", "Unknown"),
        )

    @property
    def unique_id(self):
        return f"{self.coordinator.entry.entry_id}_autodiscover"

    @property
    def is_on(self) -> bool:
        """Get discovery preference from options."""
        return self.coordinator.entry.options.get(
            self._key, True
        )

    async def async_turn_on(self) -> None:
        """Enable discovery."""
        new_options = dict(self.coordinator.entry.options)
        new_options[self._key] = True
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )

    async def async_turn_off(self) -> None:
        """Disable discovery."""
        new_options = dict(self.coordinator.entry.options)
        new_options[self._key] = False
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )

class TVPowerSaveSwitch(CoordinatorEntity, SwitchEntity):
    """Enable power-saving mode for TV control."""

    def __init__(self, coordinator: CouchsideCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._attr_name = "TV Power Save"
        self._attr_icon = "mdi:power-sleep"
        self._attr_has_entity_name = True
        self._key = "tv_power_save"

    @property
    def device_info(self) -> DeviceInfo:
        status = self.coordinator.data.get("status", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=_device_name(status),
            manufacturer="EmeryTech",
            model=status.get("os", {}).get("name", "Unknown"),
            hw_version=status.get("os", {}).get("build", "Unknown"),
            sw_version=status.get("agent_version", "Unknown"),
        )

    @property
    def unique_id(self):
        return f"{self.coordinator.entry.entry_id}_tv_powersave"

    @property
    def is_on(self) -> bool:
        """Get power-save preference from options."""
        return self.coordinator.entry.options.get(
            self._key, False
        )

    async def async_turn_on(self) -> None:
        """Enable power saving mode."""
        new_options = dict(self.coordinator.entry.options)
        new_options[self._key] = True
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )

    async def async_turn_off(self) -> None:
        """Disable power saving mode."""
        new_options = dict(self.coordinator.entry.options)
        new_options[self._key] = False
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )