"""Couchside TV controls (power, volume, input)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from homeassistant.helpers.update_coordinator import CoordinatorEntity # type: ignore

from .const import DOMAIN # type: ignore
from .coordinator import CouchsideCoordinator # type: ignore

async def async_setup_entry(hass, entry, async_add_entities):
    """Create TV control entities from /api/tv capability."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    tv_data = coordinator.data.get("tv", {})
    if not tv_data or not isinstance(tv_data, dict):
        return
    
    entities = []
    
    entities.append(CouchsideTVButton(coordinator, "power_toggle", "Power Toggle", "mdi:power"))
    entities.append(CouchsideTVButton(coordinator, "power_on", "Power On", "mdi:power-on"))
    entities.append(CouchsideTVButton(coordinator, "power_off", "Power Off", "mdi:power-off"))
    
    entities.append(CouchsideTVButton(coordinator, "vol_up", "Volume Up", "mdi:volume-plus"))
    entities.append(CouchsideTVButton(coordinator, "vol_down", "Volume Down", "mdi:volume-minus"))
    entities.append(CouchsideTVButton(coordinator, "vol_mute", "Mute", "mdi:volume-mute"))
    
    entities.append(CouchsideTVButton(coordinator, "input_hdmi", "HDMI Input", "mdi:import"))
    
    async_add_entities(entities, update_before_add=True)

def _device_name(status: dict) -> str:
    """Format a polished device name from hostname and OS."""
    hostname = status.get("hostname", "Couchside").title()
    os_name = status.get("os", {}).get("name", "")
    if os_name:
        return f"{hostname} ({os_name})"
    return hostname

class CouchsideTVButton(CoordinatorEntity, ButtonEntity):
    """A TV control button for the Couchside box."""

    def __init__(self, coordinator: CouchsideCoordinator, action_id: str, name: str, icon: str):
        CoordinatorEntity.__init__(self, coordinator)
        self.action_id = action_id
        self._attr_name = name
        self._attr_icon = icon
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
        return f"{self.coordinator.entry.entry_id}_tv_{self.action_id}"

    async def async_press(self) -> None:
        """Execute the TV action through /api/tv/<action>."""
        try:
            await self.coordinator.async_tv_command(self.action_id)
        except Exception:
            pass