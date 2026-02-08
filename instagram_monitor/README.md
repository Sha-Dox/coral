# 📸 Instagram Monitor

> Part of [CORAL](https://github.com/yourusername/coral) - Centralised OSINT Repository and Automation Layer

Real-time OSINT tool for tracking Instagram user activities and profile changes.

## 🎯 Features

- Track user posts, stories, and reels
- Monitor profile changes (bio, name, avatar)
- Track follower/following counts
- Session management (with/without login)
- Optional CORAL integration for unified dashboard

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Instagram account (optional, for advanced features)

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/instagram_monitor.git
cd instagram_monitor
pip install -r requirements.txt
```

### Basic Usage

```bash
python3 instagram_monitor.py
```

## 📋 Configuration

See the configuration section in `instagram_monitor.py` file.

## 🔌 Optional: CORAL Integration

This monitor can optionally integrate with CORAL (Centralised OSINT Repository and Automation Layer) for unified monitoring across multiple platforms.

To integrate with CORAL:
1. Copy `coral_notifier.py` from the CORAL project
2. Configure webhook settings
3. The monitor will auto-detect and connect to CORAL

See: https://github.com/YOUR_USERNAME/coral

## 📄 License

See LICENSE file.

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Respect Instagram's Terms of Service and applicable laws.
