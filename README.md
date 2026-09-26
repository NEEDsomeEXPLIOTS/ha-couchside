# Home Assistant Couchside Integration
## Custom Home Assistant integration for Couchside, an open-source LAN-only remote control agent for SteamOS, Bazzite, and Linux gaming boxes.

Couchside lets you monitor and control your gaming PC, Steam Deck or Steam Machine from Home Assistant using a bearer-token-authenticated HTTP API with optional TLS encryption.

## Features

✅ **Auto-discovery** — broadcasts UDP probe on port 8787 to find boxes

✅ **Bearer-token auth** — secure LAN-only pairing via Home Assistant config

✅ **Comprehensive sensors** — CPU temperature, memory, load, disk usage, uptime

✅ **Action buttons** — execute configured Couchside actions

✅ **Media controls** — play, pause, next, previous for MPRIS players

✅ **TV controls** — power, volume, mute, input selection (when available)

✅ **Grouped device** — all entities under one polished device entry

# Installation
## HACS
Not yet in the official HACS directory. 

## Install manually:
Download this repository as a ZIP

Extract to `config/custom_components/couchside/`

Restart Home Assistant

Go to `Settings` → `Devices & Services` → `Create Automation` → `Couchside`

## Git
`cd /config/custom_components`

`git clone https://github.com/NEEDsomeEXPLIOTS/ha-couchside couchside`

Then restart Home Assistant.

# Setup (Must already have Couchside Setup)
### 1. Get your Couchside token
On your gaming machine (SteamOS, Bazzite, or Linux with Couchside installed):

`cat /etc/couchside/token`

Copy this token. It's the bearer credential that Home Assistant will use.

### 2. Add the integration
Go to `Settings` → `Devices & Services`

Click Create Integration and search for Couchside

The integration auto-discovers boxes on your LAN (via UDP broadcast)

Paste the token from step 1

The integration will verify the token against `/api/status` and create a config entry.

### 3. Rename the device (optional)

# After setup:

Go to `Settings` → `Devices & Services`

Find the Couchside device - `Steamdeck (SteamOS)` by default

Click the device name to rename it

## Entities Created

### Sensors

**CPU Temperature** — current CPU temp in °C

**Memory Used** — RAM usage as a percentage

**Uptime** — formatted as Xd Yh Zm (days, hours, minutes)

**Load Average** — 1-minute Linux load average

**Disk Usage** — percentage used for each mount (/, /home, etc.)

### Buttons

**Couchside Actions** — one button per configured action (e.g., "Restart Session", "Reboot")

**TV Controls** — power, volume, mute, input (if TV backend is available)

### Media Players

One media player entity per active MPRIS player (Spotify, Firefox, VLC, etc.)

**Supports:** play, pause, next, previous

# Security
⚠️ Couchside is designed for trusted home LANs only. Do not expose it to the Internet.

Bearer token is stored in Home Assistant's secure credential storage

All requests use HTTP (plaintext on LAN; TLS support available in newer Couchside versions)

No client-supplied commands — all actions are allowlisted by the agent

Token is never logged or committed

## API Compatibility

**Agent version:** 2.9.88+

**Tested on:** SteamOS 3.8.28 (Steam Deck), Bazzite

**Minimum Home Assistant:** 2024.11.0

# Troubleshooting

## Integration won't load

Check the Couchside agent is running: `systemctl status couchside`

Verify the token is correct: `curl -H "Authorization: Bearer YOUR_TOKEN" http://BOX_IP:8787/api/status`

Check Home Assistant logs: `Settings` → `System` → `Logs`

### Discovery doesn't find boxes

Ensure your Home Assistant and gaming box are on the same LAN

Check firewall rules for UDP port 8787

Try manual entry with the box's IP address

### Entities show "unavailable"

Verify the token is still valid

Ensure the Couchside agent is running on the box

Check network connectivity

# Development
### AI Use
This is made by AI.

### This integration uses:
async/await patterns for Home Assistant integration standards

DataUpdateCoordinator for efficient polling (30-second interval)

Device grouping with DeviceInfo and _attr_has_entity_name

Bearer token auth with no hardcoded credentials

## License
MIT. See LICENSE.

# Links
Couchside: https://github.com/emerytech/couchside

Home Assistant docs: https://developers.home-assistant.io/

Issue tracker: https://github.com/NEEDsomeEXPLIOTS/ha-couchside/issues
