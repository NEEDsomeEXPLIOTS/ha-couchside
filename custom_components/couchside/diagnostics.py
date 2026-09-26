"""Diagnostics support for Couchside integration."""
from __future__ import annotations

import dataclasses
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DOMAIN
from .coordinator import CouchsideCoordinator


TO_REDACT = {
    CONF_TOKEN,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data
    
    return {
        "config_entry": {
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
            "entry_id": entry.entry_id[:8],  # Partial ID for privacy
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "device_info": {
            "identifiers": list(data.get("status", {}).get("hostname", "unknown")),
            "manufacturer": "EmeryTech",
            "model": data.get("status", {}).get("os", {}).get("name"),
            "sw_version": data.get("status", {}).get("agent_version"),
        },
        "connection": {
            "host": entry.data.get(CONF_HOST),
            "port": entry.data.get(CONF_PORT),
            "last_update_success": coordinator.last_update_success,
            "last_update_error": str(coordinator.last_exception) if coordinator.last_exception else None,
            "update_interval_seconds": coordinator.update_interval.total_seconds() if coordinator.update_interval else None,
        },
        "api_data": {
            "status_keys": list(data.get("status", {}).keys()) if data.get("status") else [],
            "actions_count": len(data.get("actions", {}).get("actions", [])),
            "media_players": [
                p.get("identity", p.get("id")) 
                for p in data.get("media", {}).get("players", [])
            ],
            "tv_available": bool(data.get("tv")),
        },
        "sensor_summary": {
            "cpu_temp_c": data.get("status", {}).get("cpu_temp_c"),
            "uptime_s": data.get("status", {}).get("uptime_s"),
            "mem_mb": data.get("status", {}).get("mem", {}),
            "load_avg": data.get("status", {}).get("load"),
            "disk_mounts": [
                d.get("mount") 
                for d in data.get("status", {}).get("disks", [])
            ],
        },
        "coordinator_stats": {
            "poll_count": coordinator.poll_count if hasattr(coordinator, 'poll_count') else None,
            "avg_response_time_ms": coordinator.avg_response_ms if hasattr(coordinator, 'avg_response_ms') else None,
        },
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device_id: str
) -> dict[str, Any]:
    """Return diagnostics for a device."""
    return await async_get_config_entry_diagnostics(hass, entry)