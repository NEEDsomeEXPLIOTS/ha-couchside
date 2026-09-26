"""Configured Couchside actions as Home Assistant buttons."""
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CouchsideButton(coordinator, action) for action in coordinator.data.get("actions", {}).get("actions", coordinator.data.get("actions", [])) if isinstance(action, dict)])

class CouchsideButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, action):
        super().__init__(coordinator); self.action = action; self._attr_name = f"Couchside {action.get('label', action.get('id', 'Action'))}"; self._attr_icon = "mdi:gesture-tap-button"
    @property
    def unique_id(self): return f"{self.coordinator.entry.entry_id}_action_{self.action.get('id')}"
    async def async_press(self): await self.coordinator.async_action(self.action["id"])
