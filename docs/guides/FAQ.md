# FAQ - Frequently Asked Questions

## General

### What is CORAL?

CORAL (Centralised OSINT Repository and Automation Layer) is a unified monitoring dashboard that consolidates multiple OSINT tools into a single interface. It allows you to monitor Instagram, Pinterest, Spotify, and other platforms from one place.

### Do I need to use the hub?

No! Each monitor (Instagram, Pinterest, Spotify) works completely independently. The hub is optional and provides a unified view when you want to monitor multiple people across different platforms.

### Is it free?

Yes, CORAL is 100% free and open source under the MIT License.

---

## Installation & Setup

### What do I need to run CORAL?

- Python 3.8 or higher
- Linux, macOS, or Windows
- ~100MB disk space
- Internet connection for monitors

### How do I install it?

```bash
git clone https://github.com/Sha-Dox/coral.git
cd coral
./setup.sh
./start_all.sh
```

See [README.md](../../README.md) for detailed instructions.

### Can I run it in Docker?

Yes! Use the included docker-compose.yml:
```bash
docker-compose up -d
```

---

## Usage

### How do I add a person to monitor?

1. Start CORAL: `./start_all.sh`
2. Open http://localhost:3456
3. Go to Settings tab
4. Click "Add Person"
5. Enter name and link platform usernames

### How often does it check for updates?

Default: Every 5 minutes (300 seconds)

Change in `config.yaml`:
```yaml
instagram:
  check_interval: 300  # seconds
```

### Can I trigger checks manually?

Yes! Three ways:
1. Web UI → Settings → Click "Trigger" button
2. Command line (hub): `curl -X POST http://localhost:3456/api/platforms/<id>/trigger`
3. Per platform:
   - Instagram: `curl -X POST http://localhost:8000/api/trigger-check`
   - Pinterest: `curl -X POST http://localhost:5001/api/check-now`

### How do I export data?

Currently: Export from database directly
```bash
sqlite3 coral/coral.db ".dump events" > events.sql
```

CSV export feature coming soon!

---

## Configuration

### Where is the configuration file?

`config.yaml` in the project root.

### How do I change ports?

Edit `config.yaml`:
```yaml
coral:
  port: 3456  # Change to desired port
```

Then restart: `./start_all.sh`

### Can I disable a monitor?

Yes, in `config.yaml`:
```yaml
instagram:
  enabled: false  # Disable Instagram
```

### How do I run monitors without the hub?

```bash
./start_monitors_only.sh
```

Or force standalone in config:
```yaml
instagram:
  standalone: true
```

---

## Data & Privacy

### Where is data stored?

- Database: `coral/coral.db` (SQLite)
- Logs: `/tmp/*.log` or `logs/`
- Backups: `backups/`

### Is my data encrypted?

The database is not encrypted by default. For security:
- Run CORAL on a private network
- Use file system encryption
- Limit access with firewalls

### How long is data kept?

Default: Forever

To clean old data:
```bash
sqlite3 coral/coral.db "DELETE FROM events WHERE created_at < datetime('now', '-90 days');"
```

### Can I backup my data?

Yes:
```bash
./backup.sh
```

Backups are stored in `backups/` directory.

---

## Monitors

### Which platforms are supported?

Currently:
- Instagram
- Pinterest
- Spotify

More coming soon! See [ADDING_NEW_MONITORS.md](ADDING_NEW_MONITORS.md) to add your own.

### Do monitors require API keys?

It depends:
- **Instagram**: Can work without (limited features)
- **Pinterest**: No API key needed
- **Spotify**: Requires authentication

### Can I add my own monitor?

Yes! See [ADDING_NEW_MONITORS.md](ADDING_NEW_MONITORS.md) for a complete guide.

### Why isn't my monitor connecting to CORAL?

Check:
1. Is CORAL running? `curl http://localhost:3456/api/health`
2. Is webhook URL correct in config.yaml?
3. Check monitor logs: `tail -f /tmp/*_monitor.log`

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help.

---

## Technical

### What database does it use?

SQLite - a lightweight, file-based database. No separate database server needed.

### Can I use PostgreSQL/MySQL?

Not currently, but it's on the roadmap. SQLite works great for single-user deployments.

### How do I update CORAL?

```bash
git pull
./setup.sh  # Update dependencies
./start_all.sh
```

### Is there an API?

Yes! See [API.md](../api/API.md) for complete documentation.

### Can I run multiple instances?

Yes, but they'll need separate databases and ports. Easier to just run one instance with multiple monitors.

---

## Troubleshooting

### CORAL won't start

- Check port isn't in use: `lsof -ti:3456`
- Check logs: `tail -f /tmp/coral.log`
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### No events showing up

1. Check monitors are running: `ps aux | grep monitor`
2. Verify webhook URLs in config.yaml
3. Test manually: See [API.md](../api/API.md)

### High CPU/memory usage

- Increase `check_interval` in config.yaml
- Clean old events from database
- Check for stuck processes

### More issues?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

---

## Contributing

### Can I contribute?

Yes! Contributions are welcome. See [CONTRIBUTING.md](../contributing/CONTRIBUTING.md).

### How do I report bugs?

Create an issue on GitHub: https://github.com/Sha-Dox/coral/issues

### Can I request features?

Yes! Use the feature request template on GitHub.

---

## Legal & Ethical

### Is this legal?

CORAL is a tool. Legality depends on HOW you use it:
- ✅ Monitoring your own accounts
- ✅ Monitoring public information
- ✅ Monitoring with consent
- ❌ Stalking or harassment
- ❌ Violating terms of service
- ❌ Unauthorized access

Use responsibly and ethically.

### What about privacy?

- Only monitor publicly available information
- Respect privacy laws in your jurisdiction
- Don't use for harassment or stalking
- Be transparent when monitoring others

### Terms of Service?

Many platforms prohibit automated access. Use at your own risk. Read and comply with platform terms of service.

---

## Getting Help

### Where can I get help?

1. Check this FAQ
2. Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Search existing issues on GitHub
4. Create a new issue with details

### How do I contact the developer?

- GitHub Issues: https://github.com/Sha-Dox/coral/issues
- GitHub Discussions: https://github.com/Sha-Dox/coral/discussions

---

## Roadmap

### What's coming next?

- More platforms (Twitter, TikTok, LinkedIn)
- CSV/JSON export
- Email/Slack notifications
- Web-based configuration
- Mobile app
- Cloud deployment guides

### When will X feature be ready?

Check the GitHub roadmap and milestones. No ETAs but contributions welcome!

---

**Still have questions?** Ask on GitHub Discussions!
