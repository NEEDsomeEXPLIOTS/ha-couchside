"""Constants for Couchside."""
from homeassistant.const import Platform

DOMAIN = "couchside"
DEFAULT_PORT = 8787
DISCOVERY_MAGIC = b"COUCHSIDE_DISCOVER?"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_TOKEN = "token"
PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.MEDIA_PLAYER]
