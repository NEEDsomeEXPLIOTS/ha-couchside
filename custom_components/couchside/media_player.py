"""Couchside MPRIS media player."""
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.const import STATE_IDLE, STATE_PAUSED, STATE_PLAYING
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CouchsideMediaPlayer(coordinator, p) for p in coordinator.data.get("media", {}).get("players", [])])

class CouchsideMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    def __init__(self, coordinator, player):
        super().__init__(coordinator); self.player = player; self._attr_name = f"Couchside {player.get('identity', player.get('id', 'Media'))}"; self._attr_supported_features = MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.PAUSE | MediaPlayerEntityFeature.NEXT_TRACK | MediaPlayerEntityFeature.PREVIOUS_TRACK
    @property
    def unique_id(self): return f"{self.coordinator.entry.entry_id}_media_{self.player.get('id')}"
    @property
    def state(self):
        status = self.player.get("status", "").lower()
        return STATE_PLAYING if status == "playing" else STATE_PAUSED if status == "paused" else STATE_IDLE
    @property
    def media_title(self): return self.player.get("title")
    @property
    def media_artist(self): return self.player.get("artist")
    async def _command(self, op): await self.coordinator.async_media_command(self.player["id"], op)
    async def async_media_play(self): await self._command("play")
    async def async_media_pause(self): await self._command("pause")
    async def async_media_next_track(self): await self._command("next")
    async def async_media_previous_track(self): await self._command("previous")
