"""Constants for Couchside integration."""
from homeassistant.const import Platform

DOMAIN = "couchside"
DEFAULT_PORT = 8787
DISCOVERY_MAGIC = b"COUCHSIDE_DISCOVER?"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_TOKEN = "token"
CONF_CPU_TEMP_THRESHOLD = "cpu_temp_threshold"
CONF_ENABLE_NOTIFICATIONS = "enable_notifications"
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SWITCH,
]