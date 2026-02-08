# 🔧 Standalone Monitor Usage

You can use any OSINT monitor independently without the central hub.

## Quick Start

### Clone and enter the repo
```bash
git clone https://github.com/Sha-Dox/coral.git
cd coral
```

### Option 1: Start Individual Monitor
```bash
./start_monitor.sh instagram
./start_monitor.sh pinterest
./start_monitor.sh spotify
```

### Option 2: Start All Monitors (No Hub)
```bash
./start_monitors_only.sh
```

### Option 3: Use Original Monitor Scripts
```bash
# Instagram
cd instagram_monitor
python3 instagram_monitor.py --web-dashboard --web-dashboard-port 8000

# Pinterest
cd pinterest_monitor
python3 app.py

# Spotify
cd spotify_monitor
python3 spotify_monitor.py --config-file spotify_profile_monitor.conf
```

## Configuration for Standalone Mode

### Edit config.yaml

**Option A: Disable webhooks (keep hub running, but monitors work independently)**
```yaml
instagram:
  enabled: true
  standalone: false
  webhook:
    enabled: false    # ← Set to false
```

**Option B: Set standalone mode (monitors ignore hub completely)**
```yaml
instagram:
  enabled: true
  standalone: true    # ← Set to true
```

**Option C: Disable hub entirely**
```yaml
hub:
  enabled: false      # ← Disable hub

instagram:
  enabled: true       # Monitors still work
pinterest:
  enabled: true
spotify:
  enabled: true
```

## Use Cases

### 1. Just Instagram Monitoring
```bash
# Edit config.yaml
hub:
  enabled: false
instagram:
  enabled: true
  standalone: true
pinterest:
  enabled: false
spotify:
  enabled: false

# Start
./start_monitor.sh instagram
```

### 2. Pinterest + Spotify (No Instagram, No Hub)
```bash
# Edit config.yaml
hub:
  enabled: false
instagram:
  enabled: false
pinterest:
  enabled: true
  standalone: true
spotify:
  enabled: true
  standalone: true

# Start
./start_monitors_only.sh
```

### 3. All Monitors Independently (No Hub)
```bash
# Edit config.yaml
hub:
  enabled: false
instagram:
  standalone: true
pinterest:
  standalone: true
spotify:
  standalone: true

# Start
./start_monitors_only.sh
```

## Scripts Reference

### start_monitor.sh
Start a single monitor in standalone mode.

```bash
./start_monitor.sh instagram
./start_monitor.sh pinterest
./start_monitor.sh spotify
```

**Features:**
- ✅ Checks if port is available
- ✅ Prompts to kill existing process
- ✅ Runs in background (nohup)
- ✅ Shows logs location
- ✅ Displays PID for easy stopping

**Example:**
```bash
$ ./start_monitor.sh instagram
╔════════════════════════════════════════════════════════════╗
║           Starting Instagram Monitor (Standalone)          ║
╚════════════════════════════════════════════════════════════╝

Starting Instagram Monitor...
✓ Started successfully

Monitor:  Instagram
Port:     8000
PID:      12345
Logs:     /tmp/instagram_standalone.log

Mode:     STANDALONE (no webhooks to hub)

View logs: tail -f /tmp/instagram_standalone.log
Stop:      kill 12345
```

### start_monitors_only.sh
Start all enabled monitors without the hub.

```bash
./start_monitors_only.sh
```

**Features:**
- ✅ Reads enabled status from config.yaml
- ✅ Only starts enabled monitors
- ✅ Skips hub entirely
- ✅ Shows summary of started monitors

### start_all.sh (Modified)
Now respects `enabled` flags in config.yaml.

```bash
./start_all.sh
```

**Features:**
- ✅ Starts hub if `hub.enabled: true`
- ✅ Starts each monitor if `{monitor}.enabled: true`
- ✅ Shows which services are disabled
- ✅ Dynamic kill command based on what's running

## Configuration Options

### hub.enabled
Enable/disable the central hub.
```yaml
hub:
  enabled: true   # Start hub with ./start_all.sh
  enabled: false  # Skip hub
```

### {monitor}.enabled
Enable/disable individual monitors.
```yaml
instagram:
  enabled: true   # Start this monitor
  enabled: false  # Skip this monitor
```

### {monitor}.standalone
Run monitor independently (ignore hub).
```yaml
instagram:
  standalone: true   # Don't send webhooks, work independently
  standalone: false  # Normal mode, send events to hub
```

### {monitor}.webhook.enabled
Control webhook sending.
```yaml
instagram:
  webhook:
    enabled: true   # Send events to hub
    enabled: false  # Don't send events to hub
```

## Examples

### Example 1: Instagram Only (Original Functionality)
```yaml
hub:
  enabled: false

instagram:
  enabled: true
  standalone: true
  port: 8000

pinterest:
  enabled: false

spotify:
  enabled: false
```

Then:
```bash
./start_monitor.sh instagram
# or
cd instagram_monitor && python3 instagram_monitor.py
```

### Example 2: All Monitors Independently
```yaml
hub:
  enabled: false

instagram:
  enabled: true
  standalone: true

pinterest:
  enabled: true
  standalone: true

spotify:
  enabled: true
  standalone: true
```

Then:
```bash
./start_monitors_only.sh
```

### Example 3: Hub + Monitors (Integrated Mode)
```yaml
hub:
  enabled: true

instagram:
  enabled: true
  standalone: false  # Send to hub
  webhook:
    enabled: true

pinterest:
  enabled: true
  standalone: false
  webhook:
    enabled: true

spotify:
  enabled: true
  standalone: false
  webhook:
    enabled: true
```

Then:
```bash
./start_all.sh  # Everything works together
```

### Example 4: Mixed Mode
```yaml
hub:
  enabled: true

instagram:
  enabled: true
  standalone: false   # Works with hub
  webhook:
    enabled: true

pinterest:
  enabled: true
  standalone: true    # Independent
  webhook:
    enabled: false

spotify:
  enabled: false      # Disabled
```

## Logs

Each monitor has its own log file:

### When using start_monitor.sh
```bash
tail -f /tmp/instagram_standalone.log
tail -f /tmp/pinterest_standalone.log
tail -f /tmp/spotify_standalone.log
```

### When using start_monitors_only.sh
```bash
tail -f /tmp/instagram_monitor.log
tail -f /tmp/pinterest_monitor.log
tail -f /tmp/spotify_monitor.log
```

### When using start_all.sh
```bash
tail -f /tmp/coral.log
tail -f /tmp/instagram_trigger.log
tail -f /tmp/pinterest_monitor.log
tail -f /tmp/spotify_trigger.log
```

## Stopping Services

### Individual Monitor
```bash
# Find PID
lsof -ti:8000  # Instagram port

# Kill it
kill <PID>
```

### All Monitors
```bash
# Find all PIDs
lsof -ti:8000,5001,8001

# Kill specific ports
kill $(lsof -ti:8000)  # Instagram
kill $(lsof -ti:5001)  # Pinterest
kill $(lsof -ti:8001)  # Spotify
```

### Everything (Hub + Monitors)
```bash
# Start script shows kill command
# Example: kill 12345 12346 12347 12348
```

## Benefits of Standalone Mode

✅ **No dependencies** - Run monitors without hub
✅ **Original functionality** - Works exactly like before integration
✅ **Lightweight** - Only what you need
✅ **Independent** - Each monitor has its own database/state
✅ **Flexible** - Mix standalone and integrated modes
✅ **Easy migration** - Keep existing workflows

## Migration from Original Setup

If you were using monitors independently before:

**No changes needed!** Your monitors still work exactly the same.

```bash
# Still works
cd instagram_monitor
python3 instagram_monitor.py

# Or use new scripts
./start_monitor.sh instagram
```

**To add hub integration later:**
```yaml
instagram:
  standalone: false
  webhook:
    enabled: true
```

Then `./start_all.sh` to use both.

## Summary

| Mode | Config | Command | Use Case |
|------|--------|---------|----------|
| **Single monitor** | `standalone: true` | `./start_monitor.sh instagram` | Just Instagram |
| **All monitors** | `hub.enabled: false` | `./start_monitors_only.sh` | All monitors, no hub |
| **Integrated** | `webhook.enabled: true` | `./start_all.sh` | Full system with hub |
| **Mixed** | Per-monitor config | `./start_all.sh` | Some standalone, some integrated |
| **Original** | N/A | `python3 monitor.py` | Classic usage |

---

**Bottom line:** You can use each tool exactly like before - no hub required! 🎉
