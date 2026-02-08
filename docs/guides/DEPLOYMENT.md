# Deployment Guide

## Quick Deploy with Docker

```bash
docker-compose up -d
```

Access at http://localhost:3333

---

## Manual Deployment

### 1. Install Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip sqlite3

# Install CORAL
./setup.sh
```

### 2. Configure

Edit `config.yaml` with your settings.

### 3. Run

```bash
./start_all.sh
```

---

## Production Deployment

### Using systemd (Linux)

```bash
# Copy service file
sudo cp systemd/coral.service /etc/systemd/system/

# Create user
sudo useradd -r -s /bin/false coral

# Set permissions
sudo chown -R coral:coral /opt/coral

# Enable and start
sudo systemctl enable coral
sudo systemctl start coral

# Check status
sudo systemctl status coral
```

### Using Docker Compose

```bash
# Production compose file
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f

# Update
docker-compose pull
docker-compose up -d
```

---

## Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name coral.yourdomain.com;

    location / {
        proxy_pass http://localhost:3333;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Security Checklist

- [ ] Change default ports
- [ ] Use reverse proxy with SSL
- [ ] Enable firewall
- [ ] Set up backups
- [ ] Configure log rotation
- [ ] Use environment variables for secrets
- [ ] Limit database file permissions
- [ ] Monitor system resources

---

## Monitoring

### Health Check

```bash
curl http://localhost:3333/api/health
```

### Logs

```bash
# systemd
sudo journalctl -u coral -f

# Docker
docker-compose logs -f

# Files
tail -f logs/coral.log
```

---

## Backup Strategy

### Automated Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/coral/backup.sh

# Weekly cleanup
0 3 * * 0 find /opt/coral/backups -name "*.tar.gz" -mtime +30 -delete
```

### Manual Backup

```bash
./backup.sh
```

---

## Scaling

### Multiple Monitors

Run monitors on separate machines, point to central CORAL:

```yaml
# monitor config.yaml
instagram:
  webhook:
    url: "http://central-coral.local:3333/api/webhook/instagram"
```

### Load Balancing

Use nginx to load balance multiple CORAL instances.

---

## Updates

```bash
# Pull latest code
git pull

# Update dependencies
./setup.sh

# Restart
./start_all.sh

# Or with systemd
sudo systemctl restart coral
```
