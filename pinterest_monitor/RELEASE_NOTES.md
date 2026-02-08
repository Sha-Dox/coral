# Release Notes - Pinterest Monitor v1.0.0

## 🎉 Initial Release

First public release of Pinterest Monitor - a real-time OSINT monitoring tool for Pinterest boards and user activity.

### Features

- **Board Monitoring**: Track Pinterest boards for new pins and activity
- **User Tracking**: Monitor all boards from specific Pinterest users
- **Web Dashboard**: Clean, responsive UI for managing monitors
- **Real-time Updates**: Automatic scheduled checks with configurable intervals
- **History Tracking**: View pin count changes over time with visual graphs
- **Manual Triggers**: Force checks on-demand via UI or API
- **CORAL Integration**: Optional integration with CORAL OSINT platform
- **RESTful API**: Full API for automation and integration

### Installation

Multiple installation methods supported:

```bash
# Quick install from GitHub
pip install git+https://github.com/Sha-Dox/pinterest-monitor.git

# Or download and install
wget https://github.com/Sha-Dox/pinterest-monitor/archive/refs/tags/v1.0.0.tar.gz
tar -xzf v1.0.0.tar.gz
cd pinterest-monitor-1.0.0
pip install .
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

### Quick Start

```bash
# Copy config template
cp config.example.ini config.ini

# Edit config.ini with your settings

# Run
python app.py
```

Open http://localhost:5001 in your browser.

### API Endpoints

- `GET /api/boards` - List all monitored boards
- `POST /api/add-board` - Add a board to monitor
- `POST /api/add-user` - Add all boards for a user
- `POST /api/check-now` - Trigger manual check
- `GET /api/stats` - Get statistics
- And more...

### Requirements

- Python 3.7+
- Flask
- BeautifulSoup4
- Requests
- APScheduler

### Configuration

All settings in `config.ini`:
- Check interval (default: 5 minutes)
- Server port (default: 5001)
- CORAL integration toggle
- Debug mode

### What's Next

See the [GitHub Issues](https://github.com/Sha-Dox/pinterest-monitor/issues) for planned features and improvements.

### Support

- 📖 [README](README.md)
- 📦 [Installation Guide](INSTALL.md)
- 🐛 [Report Issues](https://github.com/Sha-Dox/pinterest-monitor/issues)

### License

MIT License - See [LICENSE](LICENSE) file for details.

### Disclaimer

This tool is for educational and research purposes only. Please respect Pinterest's Terms of Service and robots.txt when using this tool.
