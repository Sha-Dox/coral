# Copilot Instructions for CORAL

## Build, Run, Lint
- Install deps: `./setup.sh` or `make install`
- Run hub + monitors: `./start_all.sh`
- Run one monitor: `./start_monitor.sh <instagram|pinterest|spotify>`
- Run monitors only: `./start_monitors_only.sh`
- Docker: `docker-compose up -d` or `make docker-up`
- Lint (CI):  
  `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,env,.git,__pycache__,instagram_monitor,pinterest_monitor,spotify_monitor`  
  `black --check --exclude='venv|env|\.git|instagram_monitor|pinterest_monitor|spotify_monitor' .`
- Security (CI): `bandit -r . -f json -o bandit-report.json --exclude './venv,./env,./instagram_monitor,./pinterest_monitor,./spotify_monitor' || true`
- Smoke check (single check): start hub then `curl http://localhost:5002/api/health`

## Architecture (Big Picture)
- **Hub**: `coral/app.py` is a Flask API + web UI; it ingests monitor events via `POST /api/webhook/<platform>` and exposes `/api/persons`, `/api/events`, `/api/platforms`, `/api/health`.
- **Data**: `coral/database.py` uses SQLite with `platforms`, `persons`, `linked_profiles`, and `events` tables for the unified timeline and person linking.
- **Config**: `config.yaml` is the single source of truth. `config_loader.ConfigLoader` loads it and provides dot-access (e.g., `hub.port`, `instagram.webhook.url`) with `OSINT_*` env overrides.
- **Integration**: `coral_integration/` provides notifier/trigger helpers; monitors send events to the hub webhook when enabled and fall back to standalone if CORAL isn’t reachable.

## Key Conventions
- After changing ports or trigger URLs in `config.yaml`, run `python3 coral/update_config.py` to sync platform trigger URLs in the DB.
- Monitors respect `standalone` and `webhook.enabled` in `config.yaml`; integrated mode is webhook-driven.
- When adding a new monitor, update `config.yaml`, add the platform default in `coral/database.py`, and wire the webhook endpoint in the hub.
