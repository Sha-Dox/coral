# Troubleshooting Guide

## Common Issues

### CORAL Won't Start

**Error: Port already in use**
```
Address already in use
Port 3333 is in use
```

**Solution:**
```bash
# Find process using port
lsof -ti:3333

# Kill the process
kill $(lsof -ti:3333)

# Or change port in config.yaml
```

---

**Error: Database locked**
```
database is locked
```

**Solution:**
```bash
# Check for stale connections
fuser coral/coral.db

# If safe, remove lock
rm coral/coral.db-journal

# Restart CORAL
./start_all.sh
```

---

### Monitors Not Connecting

**Symptom:** Monitors start but don't send events to CORAL

**Check:**
1. Is CORAL running?
   ```bash
   curl http://localhost:3333/api/health
   ```

2. Check monitor logs:
   ```bash
   tail -f /tmp/instagram_monitor.log
   ```

3. Verify webhook URL in config.yaml:
   ```yaml
   instagram:
     webhook:
       url: "http://localhost:3333/api/webhook/instagram"
   ```

4. Test webhook manually:
   ```bash
   curl -X POST http://localhost:3333/api/webhook/instagram \
     -H "Content-Type: application/json" \
     -d '{"username":"test","event_type":"test","summary":"Test event"}'
   ```

---

### Docker Issues

**Container won't start**
```bash
# Check logs
docker-compose logs coral

# Rebuild images
docker-compose build --no-cache

# Start with verbose output
docker-compose up
```

**Permission denied errors**
```bash
# Fix volume permissions
sudo chown -R $(id -u):$(id -g) ./data ./logs

# Restart
docker-compose restart
```

---

### Database Issues

**Corrupt database**
```bash
# Check integrity
sqlite3 coral/coral.db "PRAGMA integrity_check;"

# If corrupt, restore from backup
cp backups/coral_backup_XXXXXX/coral.db coral/coral.db
```

**Database won't initialize**
```bash
# Remove and reinitialize
rm coral/coral.db
cd coral && python3 -c "import database; database.init_db()"
```

---

### Performance Issues

**High CPU usage**
```bash
# Check process
top -p $(pgrep -f coral)

# Check monitor intervals in config.yaml
# Increase check_interval to reduce load
```

**High memory usage**
```bash
# Check event count
sqlite3 coral/coral.db "SELECT COUNT(*) FROM events;"

# Clean old events
sqlite3 coral/coral.db "DELETE FROM events WHERE created_at < datetime('now', '-90 days');"
```

---

### Network Issues

**Can't access web UI**

1. Check if service is running:
   ```bash
   curl http://localhost:3333/api/health
   ```

2. Check firewall:
   ```bash
   # Ubuntu/Debian
   sudo ufw status
   
   # Allow port
   sudo ufw allow 3333
   ```

3. Check if binding to correct interface:
   ```yaml
   # config.yaml
   coral:
     host: "0.0.0.0"  # Listen on all interfaces
   ```

---

### API Issues

**401 Unauthorized**
- Check webhook secret in config.yaml
- Verify secret matches in monitor configuration

**429 Too Many Requests**
- Rate limit exceeded
- Wait 60 seconds or adjust rate limits in code

**500 Internal Server Error**
- Check logs: `tail -f logs/coral.log`
- Check database connectivity
- Verify all dependencies installed

---

## Debugging Tips

### Enable Debug Mode

Edit `config.yaml`:
```yaml
coral:
  debug: true
```

Restart CORAL for detailed logging.

### View Logs

```bash
# CORAL hub
tail -f /tmp/coral.log

# All services
make logs

# Docker logs
docker-compose logs -f
```

### Test Components

```bash
# Test database
cd coral && python3 -c "import database; print(database.get_all_platforms())"

# Test webhook
curl -X POST http://localhost:3333/api/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"username":"test","event_type":"test","summary":"Test"}'

# Test health
curl http://localhost:3333/api/health
```

### Check Configuration

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Print loaded config
python3 -c "from config_loader import config; print(config)"
```

---

## Getting Help

If you're still stuck:

1. Check existing issues: https://github.com/Sha-Dox/coral/issues
2. Create a new issue with:
   - Error messages
   - Logs
   - Steps to reproduce
   - Environment details
3. Include output of:
   ```bash
   python3 --version
   uname -a
   cat config.yaml
   ```

---

## Recovery Procedures

### Clean Install

```bash
# Backup data
./backup.sh

# Stop all services
make stop

# Clean everything
make clean
rm -rf data/ logs/

# Reinstall
./setup.sh
./start_all.sh
```

### Reset Database

```bash
# Backup first!
./backup.sh

# Remove database
rm coral/coral.db

# Reinitialize
cd coral && python3 database.py
```

### Factory Reset

```bash
# DANGER: Deletes all data!

# Stop services
make stop

# Remove everything
rm -rf coral/coral.db data/ logs/ backups/

# Setup fresh
./setup.sh
```
