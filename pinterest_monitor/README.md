# 📌 Pinterest Monitor

> Part of [CORAL](https://github.com/Sha-Dox/coral) - Centralised OSINT Repository and Automation Layer

Real-time OSINT monitoring tool for Pinterest boards and user activity.

## Features

- Monitor Pinterest boards for new pins
- Track pin count changes
- Web-based dashboard
- Scheduled monitoring
- Optional CORAL integration

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Flask

### Installation (bundled with CORAL)

```bash
git clone https://github.com/Sha-Dox/coral.git
cd coral/pinterest_monitor
pip install -r requirements.txt
```

📖 **[See detailed installation guide](INSTALL.md)**

### Configuration

1. Copy configuration template:
```bash
cp config.example.ini config.ini
```

2. Edit `config.ini` with your settings

### Run

```bash
python3 app.py
```

Then open http://localhost:5001 in your browser.

## 📋 Features

### Add Boards to Monitor
Add Pinterest board URLs through the web interface.

### View History
See pin count changes over time with graphs.

### Manual Checks
Trigger checks manually via the UI or API endpoint:
```bash
curl -X POST http://localhost:5001/api/check-now
```

## 🔌 Optional: CORAL Integration

This monitor can optionally integrate with CORAL (Centralised OSINT Repository and Automation Layer).

To integrate:
1. Install CORAL
2. Configure webhook in your config
3. Events will be sent to CORAL automatically

See: https://github.com/Sha-Dox/coral

## 📄 License

MIT License - See LICENSE file

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Respect Pinterest's Terms of Service.
