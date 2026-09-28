# Home Assistant Couchside Integration (Unoffical AI Coded)

Custom Home Assistant integration for [Couchside](https://github.com/emerytech/couchside), an open-source LAN-only remote control agent for SteamOS, Bazzite, and Linux gaming boxes.

**Couchside** lets you monitor and control your gaming PC from Home Assistant using a bearer-token-authenticated HTTP API with optional TLS encryption.

## Features

✅ **Auto-discovery** — broadcasts UDP probe on port 8787 to find boxes  
✅ **Bearer-token auth** — secure LAN-only pairing via Home Assistant config  
✅ **Comprehensive sensors** — CPU temperature, memory, load, disk usage, uptime  
✅ **Binary sensors** — online/offline status, thermal warnings, battery alerts  
✅ **Number entities** — configurable thresholds and limits  
✅ **Switch entities** — enable/disable notifications and features  
✅ **Action buttons** — execute configured Couchside actions  
✅ **Media controls** — play, pause, next, previous for MPRIS players  
✅ **TV controls** — power, volume, mute, input selection (when available)  
✅ **Grouped device** — all entities under one polished device entry  
✅ **Diagnostics** — export debug data for troubleshooting  
✅ **Persistent notifications** — alerts for thermal/battery conditions  

---

## Installation

### HACS Custom Repository
1. Go to HACS in Home Assistant
2. Click **⋮ (three dots) → Custom Repository**
3. Paste `https://github.com/NEEDsomeEXPLIOTS/ha-couchside/edit/main/README.md` as the URL
4. Select **Integration** as the Type and add

### Install manually:

1. Download this repository as a ZIP
2. Extract to `config/custom_components/couchside/`
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Create Automation → Couchside**

### Git

```bash
cd /config/custom_components
git clone https://github.com/NEEDsomeEXPLIOTS/ha-couchside couchside
```

Then restart Home Assistant.

---

## Setup (Prerequisites)

### 1. Install Couchside Agent First

Ensure the Couchside agent is running on your gaming machine:

```bash
sudo apt install couchside-agent  # Example command
systemctl enable --now couchside
```

### 2. Get Your Couchside Token

On your gaming machine (SteamOS, Bazzite, or Linux with Couchside installed):

```bash
cat /etc/couchside/token
```

Copy this token. It's the bearer credential that Home Assistant will use.

### 3. Add the Integration

1. Go to **Settings → Devices & Services**
2. Click **Create Integration** and search for **Couchside**
3. The integration auto-discovers boxes on your LAN (via UDP broadcast)
4. Paste the token from step 1
5. The integration will verify the token against `/api/status` and create a config entry

### 4. Rename the Device (Optional)

1. Go to **Settings → Devices & Services**
2. Find the Couchside device (named `Steamdeck (SteamOS)` by default)
3. Click the device name to rename it

---

## Entities Created

### 🔧 Sensors

| Entity | Value | Icon | Notes |
|--------|-------|------|-------|
| **CPU Temperature** | °C | 🔌 Thermometer | Current CPU temp |
| **Memory Used** | % | 💾 Memory | RAM usage percentage |
| **Uptime** | Duration | ⏰ Clock | Formatted as `Xd Yh Zm` |
| **Load Average** | Float | 📈 CPU | 1-minute Linux load average |
| **Disk Usage** | % | 💿 Hard Disk | Per-mount percentage (/, /home, etc.) |

### 🟢 Binary Sensors

| Entity | State | Icon | Trigger Condition |
|--------|-------|------|-------------------|
| **Online Status** | On/Off | ✅ Connected | Agent responds to requests |
| **Thermal Warning** | On/Off | ⚠️ Fire Alert | CPU temp exceeds threshold (default: 85°C) |
| **Battery Low** | On/Off | 🔋 Battery Alert | Battery < 20% (when applicable) |

### 🔢 Number Entities (Configurable Limits)

| Entity | Range | Default | Description |
|--------|-------|---------|-------------|
| **CPU Temp Threshold** | 50–100°C | 85°C | Alert threshold for thermal sensor |
| **Volume Limit** | 0–100% | 80% | Maximum volume for TV control (when available) |

> 💡 Changes to number entities are saved automatically to the entry options—no reload required!

### 🔄 Switch Entities (Feature Toggles)

| Entity | Default | Description |
|--------|---------|-------------|
| **Enable Notifications** | ✅ On | Receive persistent alerts for thermal/battery events |
| **Auto Discovery** | ✅ On | Automatically detect box on LAN network changes |
| **TV Power Save** | ❌ Off | Enable power-saving mode for TV backend |

### 🔘 Button Entities

| Button | Action |
|--------|--------|
| **Couchside Actions** | One button per configured action (e.g., "Restart Session", "Reboot") |
| **TV Controls** | Power toggle, power on, power off, volume up/down, mute, HDMI input |

### 🎵 Media Players

| Property | Description |
|----------|-------------|
| **One entity per MPRIS player** | Spotify, Firefox, VLC, etc. |
| **Controls** | Play, pause, next track, previous track |
| **Metadata** | Track title, artist, album art (if provided) |

---

## Configuration via Options Flow

You can reconfigure the integration without removing it:

1. Go to **Settings → Devices & Services**
2. Find your Couchside entry
3. Click **⋮ (three dots) → Configure**
4. Update:
   - Host/IP address
   - Port number
   - Bearer token
   - Notification preferences

All changes take effect immediately.

---

## Alerts & Notifications

### Thermal Alerts

Triggered when CPU temperature exceeds the configured threshold:

```yaml
# Example notification content
🔥 Couchside: Thermal Warning
⚠️ CPU temperature on Steamdeck is 92.5°C, which is +7.5°C above your 85°C threshold.
```

**To customize:**
- Change threshold via **CPU Temp Threshold** number entity
- Disable alerts via **Enable Notifications** switch

### Battery Alerts

Triggered when battery drops below 20%:

```yaml
🔋 Couchside: Battery Low
🔋 Battery level on Steamdeck is critically low at 18%. Consider charging soon.
```

### Connectivity Alerts

Firewall or network issues that disconnect the agent. Check:
- Agent is running: `systemctl status couchside`
- Port 8787 is open
- Same network segment as Home Assistant

---

## Security

> ⚠️ **Couchside is designed for trusted home LANs only. Do not expose it to the Internet.**

| Security Feature | Implementation |
|------------------|----------------|
| **Token Storage** | Encrypted in Home Assistant credential store |
| **Transport** | HTTP (LAN only); TLS available in newer agent versions |
| **Authentication** | Bearer token with per-request validation |
| **Command Execution** | Allow-listed actions only; no arbitrary commands |
| **Logging** | Token never logged or committed |
| **Redaction** | Diagnostics exports redact sensitive fields |

---

## API Compatibility

| Requirement | Version |
|-------------|---------|
| **Agent version** | 2.9.88+ |
| **Tested on** | SteamOS 3.8.28 (Steam Deck), Bazzite |
| **Minimum Home Assistant** | 2024.11.0 |
| **Polling interval** | 30 seconds (adjustable in development) |

---

## Troubleshooting

### Integration Won't Load

1. Check the Couchside agent is running:
   ```bash
   systemctl status couchside
   ```
2. Verify the token is correct:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://BOX_IP:8787/api/status
   ```
3. Check Home Assistant logs: **Settings → System → Logs**

### Discovery Doesn't Find Boxes

- Ensure Home Assistant and gaming box are on the same LAN
- Check firewall rules for UDP port 8787
- Try manual entry with the box's IP address

### Entities Show "Unavailable"

1. Verify the token is still valid
2. Ensure the Couchside agent is running on the box
3. Check network connectivity
4. Run diagnostics: **Devices & Services → Couchside → Export Diagnostics**

### Thermal Alerts Not Firing

- Confirm **Enable Notifications** switch is ON
- Check CPU Temp Threshold is set appropriately
- Review diagnostics for coordinator errors

### TV Controls Not Working

- TV backend must be available on the agent
- Some TVs may not support all IR commands
- Check agent logs for `/api/tv` endpoint errors

---

## Diagnostics

Export detailed debug data for troubleshooting:

1. Go to **Settings → Devices & Services**
2. Click **⋮ (three dots) → Download Diagnostics**
3. Share the JSON file with support

**Diagnostics include:**
- Redacted config (token masked)
- Connection status and last errors
- API data summary (sensors, actions, media players)
- Coordinator stats (poll count, response times)
- Device information

---

## Development

### AI Use

This integration was developed with AI assistance for rapid iteration and code generation.

### Architecture

| Component | Technology |
|-----------|------------|
| **Async Patterns** | `async/await` for non-blocking I/O |
| **Coordinator** | `DataUpdateCoordinator` with 30s polling |
| **Device Grouping** | `DeviceInfo` with `_attr_has_entity_name` |
| **Auth** | Bearer token (no hardcoded credentials) |
| **Storage** | Config Entries + Options Flow |

### Adding New Platforms

To add a new entity type:

1. Create `<platform>.py` with `async_setup_entry()`
2. Register platform in `const.py` `PLATFORMS` list
3. Implement entity classes inheriting from `CoordinatorEntity`
4. Follow Home Assistant entity guidelines

### Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Test with real hardware if possible
4. Submit pull request with clear description

---

## License

MIT. See [LICENSE](LICENSE) file.

---

## Links

- **Couchside Agent**: https://github.com/emerytech/couchside
- **Home Assistant Docs**: https://developers.home-assistant.io/
- **Issue Tracker**: https://github.com/NEEDsomeEXPLIOTS/ha-couchside/issues
- **Pull Requests**: https://github.com/NEEDsomeEXPLIOTS/ha-couchside/pulls
```
