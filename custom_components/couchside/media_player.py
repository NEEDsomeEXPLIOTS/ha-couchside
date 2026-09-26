"""Couchside media players."""
from __future__ import annotations

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.const import STATE_IDLE, STATE_PAUSED, STATE_PLAYING
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CouchsideCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    """Create a media player for each active player reported by Couchside."""
    coordinator: CouchsideCoordinator = hass.data[DOMAIN][entry.entry_id]
    players = coordinator.data.get("media", {}).get("players", [])
    entities = [
        CouchsideMediaPlayer(coordinator, player)
        for player in players
        if isinstance(player, dict) and "id" in player
    ]
    async_add_entities(entities, update_before_add=True)


class CouchsideMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """A Couchside media player entity backed by the agent's /api/media endpoint."""

    def __init__(self, coordinator: CouchsideCoordinator, player: dict):
        super().__init__(coordinator)
        self.player_id = player.get("id")
        self._attr_name = player.get("identity", player.get("id", "Media"))
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
        )
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
        return f"{self.coordinator.entry.entry_id}_media_{self.player_id}"

    @property
    def _current_player(self):
        players = self.coordinator.data.get("media", {}).get("players", [])
        return next((p for p in players if p.get("id") == self.player_id), None)

    @property
    def state(self):
        player = self._current_player
        if not player:
            return STATE_IDLE
        status = str(player.get("status", "")).lower()
        if status == "playing":
            return STATE_PLAYING
        if status == "paused":
            return STATE_PAUSED
        return STATE_IDLE

    @property
    def media_title(self):
        player = self._current_player
        return player.get("title") if player else None

    @property
    def media_artist(self):
        player = self._current_player
        return player.get("artist") if player else None

    async def _command(self, op: str, body: dict | None = None) -> None:
        await self.coordinator.async_media_command(self.player_id, op, body)

    async def async_media_play(self) -> None:
        await self._command("play")

    async def async_media_pause(self) -> None:
        await self._command("pause")

    async def async_media_next_track(self) -> None:
        await self._command("next")

    async def async_media_previous_track(self) -> None:
        await self._command("previous")
