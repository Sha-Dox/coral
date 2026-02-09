#!/usr/bin/env python3
"""CORAL - Consolidated OSINT Repository & Activity Ledger"""
import logging
import time
from flask import Flask

import config
import database as db
from scheduler import CoralScheduler
from routes.pages import bp as pages_bp
from routes.identities import bp as identities_bp
from routes.accounts import bp as accounts_bp
from routes.events import bp as events_bp
from routes.monitoring import bp as monitoring_bp
from routes.settings import bp as settings_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Cache busting: append ?v=<start_time> to static file URLs
_boot = int(time.time())

@app.context_processor
def inject_version():
    return {"v": _boot}

# Register blueprints
app.register_blueprint(pages_bp)
app.register_blueprint(identities_bp)
app.register_blueprint(accounts_bp)
app.register_blueprint(events_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(settings_bp)

# Initialize
db.init_db()
scheduler = CoralScheduler(check_interval=config.CHECK_INTERVAL)
app.config["scheduler"] = scheduler

if __name__ == "__main__":
    scheduler.start()
    print(f"\n{'=' * 50}")
    print(f"  CORAL running on http://localhost:{config.PORT}")
    print(f"{'=' * 50}\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=False)
