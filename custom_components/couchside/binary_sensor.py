"""Couchside binary sensors for status alerts."""
from __future__ import annotations

from homeassistant.components.binary_sensor import ( # type: ignore
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from homeassistant.helpers.update_coordinator import CoordinatorEntity # type: ignore

from .const import ( # type: ignore
    CONF_CPU_TEMP_THRESHOLD,
    DOMAIN,
)
from .coordinator import CouchsideCoordinator # type: ignore

async def async_setup_entry(hass, entry, async_add_entities):
    """Create binary sensor entities for Couchside box."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    status = coordinator.data.get("status", {})
    
    entities = [
        CouchsideOnlineSensor(coordinator),
        CouchsideThermalSensor(coordinator),
    ]
    
    if "battery_pct" in status or "battery_state" in status:
        entities.append(CouchsideBatterySensor(coordinator))
    
    async_add_entities(entities, update_before_add=True)

def _device_name(status: dict) -> str:
    """Format a polished device name from hostname and OS."""
    hostname = status.get("hostname", "Couchside").title()
    os_name = status.get("os", {}).get("name", "")
    if os_name:
        return f"{hostname} ({os_name})"
    return hostname

class CouchsideOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    """Online/Offline status of the Couchside agent."""

    def __init__(self, coordinator: CouchsideCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._attr_name = "Online Status"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_icon = "mdi:check-circle"
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
        return f"{self.coordinator.entry.entry_id}_online"

    @property
    def is_on(self) -> bool | None:
        """Return True if agent is reachable."""
        return self.coordinator.last_update_success

class CouchsideThermalSensor(CoordinatorEntity, BinarySensorEntity):
    """Alert when CPU temperature exceeds threshold."""

    def __init__(self, coordinator: CouchsideCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._attr_name = "Thermal Warning"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_icon = "mdi:fire-alert"
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
        return f"{self.coordinator.entry.entry_id}_thermal"

    @property
    def is_on(self) -> bool | None:
        """Return True if thermal threshold exceeded."""
        cpu_temp = self.coordinator.data.get("status", {}).get("cpu_temp_c")
        if cpu_temp is None:
            return None
        
        options = self.coordinator.entry.options
        threshold = options.get(CONF_CPU_TEMP_THRESHOLD, 85.0)
        
        return cpu_temp > threshold

    @property
    def extra_state_attributes(self):
        """Additional diagnostic info."""
        cpu_temp = self.coordinator.data.get("status", {}).get("cpu_temp_c")
        options = self.coordinator.entry.options
        threshold = options.get(CONF_CPU_TEMP_THRESHOLD, 85.0)
        return {
            "current_temperature_c": cpu_temp,
            "threshold_c": threshold,
            "state": "warning" if cpu_temp and cpu_temp > threshold else "normal",
        }

class CouchsideBatterySensor(CoordinatorEntity, BinarySensorEntity):
    """Alert when battery is low."""

    def __init__(self, coordinator: CouchsideCoordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._attr_name = "Battery Low"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY_LOW
        self._attr_icon = "mdi:battery-alert"
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
        return f"{self.coordinator.entry.entry_id}_battery_low"

    @property
    def is_on(self) -> bool | None:
        """Return True if battery is critically low."""
        battery_pct = self.coordinator.data.get("status", {}).get("battery_pct")
        if battery_pct is None:
            return None
        return battery_pct < 20

    @property
    def extra_state_attributes(self):
        """Current battery percentage."""
        return {
            "battery_percent": self.coordinator.data.get("status", {}).get("battery_pct"),
        }