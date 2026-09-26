# Home Assistant Couchside integration

Custom HACS integration for [Couchside](https://github.com/emerytech/couchside), a LAN-only agent for SteamOS, Bazzite, and Linux gaming boxes.

## Installation

Copy `custom_components/couchside` into your Home Assistant `config/custom_components/` directory, restart Home Assistant, then use **Settings → Devices & services → Add integration → Couchside**.

The integration broadcasts Couchside's `COUCHSIDE_DISCOVER?` UDP probe on port 8787. Enter the token from `/etc/couchside/token` on the box when prompted. The token is stored by Home Assistant and is never committed to this repository.

## Current entities

- CPU temperature, uptime, and load sensors
- Configured Couchside actions as buttons
- MPRIS players as media players

Screen capture is intentionally not implemented. Couchside is intended for a trusted home LAN; do not port-forward it to the Internet.
