"""Couchside action buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from homeassistant.helpers.update_coordinator import CoordinatorEntity # type: ignore

from .const import DOMAIN # type: ignore
from .coordinator import CouchsideCoordinator # type: ignore

async def async_setup_entry(hass, entry, async_add_entities):
    """Create a button entity for each configured Couchside action."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    actions = coordinator.data.get("actions", {}).get("actions", [])
    entities = [
        CouchsideButton(coordinator, action)
        for action in actions
        if isinstance(action, dict) and "id" in action
    ]
    async_add_entities(entities, update_before_add=True)

def _device_name(status: dict) -> str:
    """Format a polished device name from hostname and OS."""
    hostname = status.get("hostname", "Couchside").title()
    os_name = status.get("os", {}).get("name", "")
    if os_name:
        return f"{hostname} ({os_name})"
    return hostname

class CouchsideButton(CoordinatorEntity, ButtonEntity):
    """A Couchside box action exposed as a Home Assistant button."""

    def __init__(self, coordinator: CouchsideCoordinator, action: dict):
        CoordinatorEntity.__init__(self, coordinator)
        self.action = action
        self._attr_name = action.get("label", action.get("id", "Action"))
        self._attr_icon = "mdi:gesture-tap-button"
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
        return f"{self.coordinator.entry.entry_id}_action_{self.action.get('id')}"

    async def async_press(self) -> None:
        await self.coordinator.async_action(self.action["id"])