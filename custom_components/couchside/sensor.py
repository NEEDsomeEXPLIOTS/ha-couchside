"""Couchside status sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CouchsideCoordinator

# Static sensors expected on the Couchside box.
# The actual payload from the SteamDeck in this session reports:
# - cpu_temp_c: float
# - uptime_s: int
# - mem: {total_mb, used_mb, available_mb, ...}
# - load: [1m, 5m, 15m]
# - disks: [{mount, total_gb, used_gb, free_gb, pct}, ...]
SENSORS = {
    "cpu_temp_c": ("CPU Temperature", UnitOfTemperature.CELSIUS, "mdi:thermometer"),
    "uptime_s": ("Uptime", UnitOfTime.SECONDS, "mdi:clock-outline"),
    "mem": ("Memory Used", PERCENTAGE, "mdi:memory"),
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Create sensor entities for one Couchside box."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    status = coordinator.data.get("status", {})

    entities = [
        CouchsideSensor(coordinator, key, *meta)
        for key, meta in SENSORS.items()
    ]

    # /api/status exposes a 3-value load list: [1m, 5m, 15m].
    # This is not a percentage; it is a load-average value, so we expose it as-is.
    entities.append(CouchsideLoadSensor(coordinator, "Load Average", "mdi:cpu-64-bit"))

    for disk in status.get("disks", []):
        mount = disk.get("mount")
        if mount:
            entities.append(CouchsideDiskSensor(coordinator, mount))

    async_add_entities(entities, update_before_add=True)


class CouchsideSensor(CoordinatorEntity, SensorEntity):
    """A status sensor for a Couchside box metric."""

    def __init__(self, coordinator: CouchsideCoordinator, key: str, name: str, unit: str, icon: str):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
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
        if self.key == "mem" and isinstance(value, dict):
            total = value.get("total_mb", 0)
            used = value.get("used_mb", 0)
            if total > 0:
                return round(100 * used / total, 1)
            return None
        return value


class CouchsideLoadSensor(CoordinatorEntity, SensorEntity):
    """Expose the 1-minute load average from /api/status."""

    def __init__(self, coordinator: CouchsideCoordinator, name: str, icon: str):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_icon = icon
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
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
        return f"{self.coordinator.entry.entry_id}_load_1m"

    @property
    def native_value(self):
        load = self.coordinator.data.get("status", {}).get("load")
        if isinstance(load, list) and load:
            return float(load[0])
        return None


class CouchsideDiskSensor(CoordinatorEntity, SensorEntity):
    """Expose a given disk mount as a percentage-used sensor."""

    def __init__(self, coordinator: CouchsideCoordinator, mount: str):
        super().__init__(coordinator)
        self.mount = mount
        self._attr_name = f"Disk {mount} Used"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:harddisk"
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
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
        for disk in self.coordinator.data.get("status", {}).get("disks", []):
            if disk.get("mount") == self.mount:
                total = disk.get("total_gb", 0)
                used = disk.get("used_gb", 0)
                if total > 0:
                    return round(100 * used / total, 1)
                return None
        return None
