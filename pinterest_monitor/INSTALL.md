# Installation Guide

## Bundled with CORAL (Recommended)

```bash
git clone https://github.com/Sha-Dox/coral.git
cd coral/pinterest_monitor
pip install -r requirements.txt
```

## Configuration

1. Copy the example configuration:
```bash
cp config.example.ini config.ini
```

2. Edit `config.ini` with your settings:
```ini
[DEFAULT]
port = 5001
check_interval = 300
enable_coral = false
```

## Running

### If running from source:
```bash
python app.py
# or
./start.sh
```

### Access the dashboard:
Open http://localhost:5001 in your browser

## Troubleshooting

### Port already in use
Change the port in `config.ini`:
```ini
port = 5001
```

### Database issues
Reset the database:
```bash
python reset_db.py
```

### Missing dependencies
Reinstall requirements:
```bash
pip install -r requirements.txt --upgrade
```

## System Requirements

- Python 3.7 or higher
- 50MB disk space
- Internet connection for Pinterest API calls

## Optional: Run as a Service

### Linux (systemd)
Create `/etc/systemd/system/pinterest-monitor.service`:
```ini
[Unit]
Description=Pinterest Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/coral/pinterest_monitor
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable pinterest-monitor
sudo systemctl start pinterest-monitor
```

## Uninstall

```bash
pip uninstall pinterest-monitor
```
