# CORAL Integration Module

This directory contains **ALL** code related to CORAL hub integration. Monitors can work completely independently without these files.

## 📁 Files in this Module

### Core Integration
- **`coral_notifier.py`** - Helper to send events to CORAL (copy to your monitor)
- **`coral_checker.py`** - Auto-detection logic (checks if hub is available)
- **`config_loader.py`** - Central configuration loader

### Trigger APIs (Optional)
- **`instagram_trigger_api.py`** - Instagram manual trigger wrapper
- **`spotify_trigger_api.py`** - Spotify manual trigger wrapper
- **`pinterest_trigger_api.py`** - Pinterest manual trigger wrapper (if needed)

## 🔧 How Monitors Use This

### Option 1: Full Integration (with auto-detection)
```python
# Copy coral_notifier.py to your monitor directory
from coral_notifier import CoralNotifier

# Auto-detects CORAL availability
notifier = CoralNotifier('myplatform')

# Send events (gracefully fails if standalone)
notifier.send_event(
    username='johndoe',
    event_type='new_post',
    summary='Posted a new photo',
    data={'post_id': '123'}
)
```

### Option 2: Manual Integration (no auto-detection)
```python
from coral_notifier import CoralNotifier

# Manually specify hub URL
notifier = CoralNotifier(
    platform='myplatform',
    hub_url='http://localhost:3456/api/webhook/myplatform',
    webhook_secret='optional-secret',
    auto_detect=False
)

notifier.send_event(...)
```

### Option 3: Pure Standalone (no integration)
Don't copy any files. Your monitor works independently.

## 🚀 Adding Integration to Your Monitor

### Step 1: Copy Integration File
```bash
cp coral_integration/coral_notifier.py /path/to/your/monitor/
```

### Step 2: Add to Your Code
```python
# At the top of your monitor
try:
    from coral_notifier import CoralNotifier
    notifier = CoralNotifier('myplatform')
    HUB_ENABLED = True
except ImportError:
    HUB_ENABLED = False
    notifier = None

# When event happens
if HUB_ENABLED and notifier:
    notifier.send_event(
        username='johndoe',
        event_type='new_activity',
        summary='Activity detected'
    )
```

### Step 3: Configure (Optional)
Edit `config.yaml` at project root:
```yaml
myplatform:
  enabled: true
  standalone: false  # Set to true if you want standalone mode
  webhook:
    enabled: true
    url: "http://localhost:3456/api/webhook/myplatform"
```

## 🔄 Manual Trigger API (Optional)

If you want CORAL to trigger your monitor on-demand:

### Create trigger_api.py in your monitor
```python
from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/api/trigger', methods=['POST'])
def trigger_check():
    subprocess.Popen(['python3', 'your_monitor.py', '--check-once'])
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
```

### Add to config.yaml
```yaml
myplatform:
  port: 8002
  trigger_url: "http://localhost:8002/api/trigger"
```

## 📊 Dependency Graph

```
Your Monitor (Standalone)
    ↓ (optional)
coral_notifier.py
    ↓ (uses)
├── config_loader.py → config.yaml
└── coral_checker.py
    ↓ (checks)
CORAL Hub (if available)
```

## 🔑 Key Points

1. **Monitors are completely independent** - They work without any CORAL files
2. **Integration is opt-in** - Copy coral_notifier.py when you want integration
3. **Auto-detection is smart** - Checks if hub is available in <500ms, falls back gracefully
4. **No breaking changes** - Your monitor code doesn't break if hub is unavailable
5. **Single source of truth** - All integration code is in this directory

## 🛠️ Working on Monitors Safely

### To modify a monitor WITHOUT affecting hub:
1. Don't modify files in `coral_integration/`
2. Your monitor code is completely separate
3. If you import coral_notifier, it gracefully degrades if hub isn't available

### To modify hub integration WITHOUT affecting monitors:
1. Only edit files in `coral_integration/`
2. Keep the `CoralNotifier` interface stable
3. Test with `auto_detect=False` mode first

### To test both together:
```bash
# Terminal 1: Start hub
cd coral
python3 app.py

# Terminal 2: Start monitor (will auto-detect hub)
cd ../your_monitor
python3 monitor.py

# Terminal 3: Start without hub (standalone)
cd ../your_monitor
# Edit config.yaml: standalone: true
python3 monitor.py
```

## 📝 Contract: CoralNotifier Interface

### Methods (Stable - Don't Change)
```python
notifier = CoralNotifier(platform: str, hub_url: str = None, 
                      secret: str = None, auto_detect: bool = True)

# Core method
notifier.send_event(username: str, event_type: str, summary: str,
                   event_time: str = None, data: dict = None) -> bool

# Helper methods
notifier.send_post_event(username, caption, post_url, post_id, timestamp) -> bool
notifier.send_bio_change(username, old_bio, new_bio) -> bool
notifier.send_follower_change(username, old_count, new_count) -> bool

# Status methods
notifier.is_hub_mode() -> bool
notifier.get_mode_string() -> str  # "INTEGRATED" or "STANDALONE"
```

### Webhook Payload (Stable - Don't Change)
```json
{
  "username": "string",
  "event_type": "string", 
  "summary": "string",
  "event_time": "ISO8601 string (optional)",
  "data": {} // optional, any JSON
}
```

## 🎯 Examples

See `demo_auto_detection.py` in project root for a complete working example.
