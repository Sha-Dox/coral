# 🎵 Spotify Monitor

> Part of [CORAL](https://github.com/yourusername/coral) - Centralised OSINT Repository and Automation Layer

Real-time tracking tool for Spotify friend activity, profile changes, and playlist updates.

## 🎯 Features

- Monitor friend listening activity in real-time
- Track user profile and follower changes
- Monitor playlist updates
- Multiple authentication methods
- Optional CORAL integration

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Spotify account

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/spotify_monitor.git
cd spotify_monitor
pip install -r requirements.txt
```

### Configuration

Edit the configuration section in `spotify_monitor.py`:

```python
# Monitoring mode: 'friends', 'profile', or 'both'
MONITORING_MODE = "profile"

# Authentication method
TOKEN_SOURCE = "cookie"  # or 'oauth_app', 'oauth_user', 'client'
```

### Run

```bash
python3 spotify_monitor.py
```

## 📋 Authentication Methods

### Cookie Method (Recommended)
Extract `sp_dc` cookie from browser and set in config.

### OAuth App
Use Client Credentials flow with Spotify app credentials.

### OAuth User
Use Authorization Code flow for user-specific data.

### Client
Advanced: Use captured client credentials.

## 🔌 Optional: CORAL Integration

This monitor can optionally integrate with CORAL (Centralised OSINT Repository and Automation Layer).

To integrate:
1. Copy `coral_notifier.py` from CORAL project
2. Configure webhook settings
3. Auto-detection will connect to CORAL when available

See: https://github.com/YOUR_USERNAME/coral

## 📄 License

See LICENSE file.

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Respect Spotify's Terms of Service and applicable laws.
