"""Couchside number entities for configurable thresholds."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CPU_TEMP_THRESHOLD,
    DEFAULT_PORT,
    DOMAIN,
)
from .coordinator import CouchsideCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    """Create number entities for configurable values."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        CpuTempThresholdSensor(coordinator),
    ]
    
    # Volume limit if TV control is available
    if coordinator.data.get("tv"):
        entities.append(VolumeLimitSensor(coordinator))
    
    async_add_entities(entities, update_before_add=True)


def _device_name(status: dict) -> str:
    """Format a polished device name from hostname and OS."""
    hostname = status.get("hostname", "Couchside").title()
    os_name = status.get("os", {}).get("name", "")
    if os_name:
        return f"{hostname} ({os_name})"
    return hostname


class CpuTempThresholdSensor(NumberEntity):
    """Set the CPU temperature warning threshold."""

    def __init__(self, coordinator: CouchsideCoordinator):
        super().__init__()
        self._attr_name = "CPU Temp Threshold"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_mode = NumberMode.BOX
        self._attr_min_value = 50.0
        self._attr_max_value = 100.0
        self._attr_step = 1.0
        self._attr_icon = "mdi:thermometer-high"
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
        return f"{self.coordinator.entry.entry_id}_temp_threshold"

    @property
    def native_value(self) -> float:
        """Get threshold from entry options."""
        return self.coordinator.entry.options.get(
            CONF_CPU_TEMP_THRESHOLD, 85.0
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the threshold via options."""
        new_options = dict(self.coordinator.entry.options)
        new_options[CONF_CPU_TEMP_THRESHOLD] = round(value, 1)
        
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )


class VolumeLimitSensor(NumberEntity):
    """Set maximum volume level for TV control."""

    def __init__(self, coordinator: CouchsideCoordinator):
        super().__init__()
        self._attr_name = "Volume Limit"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_mode = NumberMode.BOX
        self._attr_min_value = 0.0
        self._attr_max_value = 100.0
        self._attr_step = 1.0
        self._attr_icon = "mdi:volume-high"
        self._attr_has_entity_name = True
        self._limit_key = "tv_volume_limit"

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
        return f"{self.coordinator.entry.entry_id}_volume_limit"

    @property
    def native_value(self) -> float:
        """Get volume limit from entry options."""
        return self.coordinator.entry.options.get(
            self._limit_key, 80.0
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the volume limit via options."""
        new_options = dict(self.coordinator.entry.options)
        new_options[self._limit_key] = round(value, 1)
        
        await self.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )