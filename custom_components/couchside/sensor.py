"""Couchside status sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CouchsideCoordinator

SENSORS = {
    "cpu_temp_c": ("CPU Temperature", UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    "uptime_s": ("Uptime", UnitOfTime.SECONDS, "mdi:clock-outline"),
    "mem": ("Memory Used", PERCENTAGE, "mdi:memory"),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        CouchsideSensor(coordinator, key, *meta) for key, meta in SENSORS.items()
    ]
    # Load average (first element of load list)
    entities.append(CouchsideSensor(coordinator, "load", "Load Average", PERCENTAGE, "mdi:cpu-64-bit"))
    
    # Disk sensors
    entities.append(CouchsideDiskSensor(coordinator, "/", "Root Disk Used", PERCENTAGE, "mdi:harddisk"))
    if "disks" in coordinator.data.get("status", {}):
        for disk_info in coordinator.data.get("status", {}).get("disks", []):
            mount = disk_info.get("mount", "/")
            if mount != "/":
                entities.append(
                    CouchsideDiskSensor(coordinator, mount, f"Disk {mount} Used", PERCENTAGE, "mdi:harddisk")
                )
    
    async_add_entities(entities)


class CouchsideSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: CouchsideCoordinator, key: str, name: str, unit: str, icon: str):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        status = self.coordinator.data.get("status", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=status.get("hostname", "Couchside"),
            manufacturer="EmeryTech",
            model=status.get("os", {}).get("name", "Unknown"),
            hw_version=status.get("os", {}).get("build", "Unknown"),
            sw_version=status.get("agent_version", "Unknown"),
        )

    @property
    def unique_id(self):
        return f"{self.coordinator.entry.entry_id}_{self.key}"

    @property
    def native_value(self):
        value = self.coordinator.data.get("status", {}).get(self.key)
        if self.key == "load" and isinstance(value, list):
            return round(value[0] * 100 / 4, 1) if value else None  # Scale to percentage
        if self.key == "mem" and isinstance(value, dict):
            total = value.get("total_mb", 0)
            used = value.get("used_mb", 0)
            return round(100 * used / total, 1) if total > 0 else None
        return value


class CouchsideDiskSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: CouchsideCoordinator, mount: str, name: str, unit: str, icon: str):
        super().__init__(coordinator)
        self.mount = mount
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        status = self.coordinator.data.get("status", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=status.get("hostname", "Couchside"),
            manufacturer="EmeryTech",
            model=status.get("os", {}).get("name", "Unknown"),
            hw_version=status.get("os", {}).get("build", "Unknown"),
            sw_version=status.get("agent_version", "Unknown"),
        )

    @property
    def unique_id(self):
        return f"{self.coordinator.entry.entry_id}_disk_{self.mount}"

    @property
    def native_value(self):
        disks = self.coordinator.data.get("status", {}).get("disks", [])
        for disk in disks:
            if disk.get("mount") == self.mount:
                total = disk.get("total_gb", 0)
                used = disk.get("used_gb", 0)
                return round(100 * used / total, 1) if total > 0 else None
        return None
