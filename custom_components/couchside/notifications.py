"""Notification service for Couchside alerts."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.persistent_notification import async_create

from .const import CONF_ENABLE_NOTIFICATIONS, DOMAIN

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
        _LOGGER.warning(f"No config entry found for {entry_id}")
        return
    
    # Check if notifications are enabled
    if not config_entry.options.get(CONF_ENABLE_NOTIFICATIONS, True):
        _LOGGER.debug(f"Notifications disabled for {entry_id}")
        return
    
    # Create the notification
    notification_id = f"couchside_{alert_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    async_create(
        hass=hass,
        message=message,
        title=f"Couchside: {alert_type.replace('_', ' ').title()}",
        notification_id=notification_id,
    )
    
    _LOGGER.info(f"Sent {severity} alert: {message}")


def format_cpu_temp_alert(
    current_temp: float,
    threshold: float,
    hostname: str,
) -> str:
    """Format a CPU temperature alert message."""
    delta = current_temp - threshold
    return (
        f"⚠️ CPU temperature on {hostname} is {current_temp:.1f}°C, "
        f"which is {delta:+.1f}°C above your {threshold}°C threshold."
    )


def format_battery_alert(battery_pct: float, hostname: str) -> str:
    """Format a battery low alert message."""
    return (
        f"🔋 Battery level on {hostname} is critically low at {battery_pct:.0f}%."
        "Consider charging soon."
    )


def format_network_alert(hostname: str, last_seen: datetime) -> str:
    """Format a network connectivity alert."""
    return (
        f"📡 Device {hostname} has gone offline. "
        f"Last seen: {last_seen.strftime('%H:%M:%S')}"
    )