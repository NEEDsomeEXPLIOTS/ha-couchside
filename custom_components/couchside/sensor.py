"""Couchside status sensors."""
from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import CouchsideCoordinator

SENSORS = {
    "cpu_temp_c": ("CPU temperature", UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    "uptime_s": ("Uptime", UnitOfTime.SECONDS, "mdi:clock-outline"),
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [CouchsideSensor(coordinator, key, *meta) for key, meta in SENSORS.items()]
    entities += [CouchsideSensor(coordinator, "load", "Load", PERCENTAGE, "mdi:cpu-64-bit")]
    async_add_entities(entities)

class CouchsideSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, icon):
        super().__init__(coordinator); self.key = key; self._attr_name = f"Couchside {name}"; self._attr_native_unit_of_measurement = unit; self._attr_icon = icon
    @property
    def unique_id(self): return f"{self.coordinator.entry.entry_id}_{self.key}"
    @property
    def native_value(self):
        value = self.coordinator.data.get("status", {}).get(self.key)
        if self.key == "load" and isinstance(value, list): return value[0] if value else None
        return value
