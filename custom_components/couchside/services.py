"""Service helpers for Couchside notifications."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.components.persistent_notification import async_create # type: ignore

from .const import CONF_ENABLE_NOTIFICATIONS, DOMAIN # type: ignore

_LOGGER = logging.getLogger(__name__)

async def send_alert_notification(
    hass: HomeAssistant,
    entry_id: str,
    alert_type: str,
    message: str,
    severity: str = "warning",
) -> None:
    """Send a persistent notification for an alert."""
    config_entry = hass.config_entries.async_get_entry(entry_id)
    if not config_entry:
        _LOGGER.warning("No config entry found for %s", entry_id)
        return
    
    if not config_entry.options.get(CONF_ENABLE_NOTIFICATIONS, True):
        _LOGGER.debug("Notifications disabled for %s", entry_id)
        return
    
    notification_id = f"couchside_{alert_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    async_create(
        hass=hass,
        message=message,
        title=f"Couchside: {alert_type.replace('_', ' ').title()}",
        notification_id=notification_id,
    )
    
    _LOGGER.info("Sent %s alert: %s", severity, message)

def format_cpu_temp_alert(
    current_temp: float,
    threshold: float,
    hostname: str,
) -> str:
    """Format a CPU temperature alert message."""
    delta = current_temp - threshold
    return (
        f"CPU temperature on {hostname} is {current_temp:.1f}°C, "
        f"which is {delta:+.1f}°C above your {threshold}°C threshold."
    )

def format_battery_alert(battery_pct: float, hostname: str) -> str:
    """Format a battery low alert message."""
    return (
        f"Battery level on {hostname} is critically low at {battery_pct:.0f}%."
        "Consider charging soon."
    )