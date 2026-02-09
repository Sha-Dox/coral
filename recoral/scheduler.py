import logging
from apscheduler.schedulers.background import BackgroundScheduler

import database as db
from monitors.pinterest import PinterestMonitor
from monitors.instagram import InstagramMonitor
from monitors.spotify import SpotifyMonitor

logger = logging.getLogger(__name__)


class CoralScheduler:
    def __init__(self, check_interval=300):
        self.scheduler = BackgroundScheduler()
        self.check_interval = check_interval
        self.is_running = False
        self.pinterest = PinterestMonitor()
        self.instagram = InstagramMonitor()
        self.spotify = SpotifyMonitor()
        self._monitors = {
            "pinterest": self.pinterest,
            "instagram": self.instagram,
            "spotify": self.spotify,
        }

    def start(self):
        if not self.is_running:
            self.scheduler.add_job(self.check_all, "interval", seconds=self.check_interval,
                                   id="check_all", replace_existing=True)
            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler started (every %ds)", self.check_interval)

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False

    def check_all(self):
        logger.info("Running scheduled check...")
        accounts = db.get_enabled_accounts()
        ok = 0
        for acc in accounts:
            monitor = self._monitors.get(acc["platform"])
            if not monitor:
                continue
            try:
                monitor.check(acc, db)
                ok += 1
            except Exception as e:
                logger.error("Check failed %s/%s: %s", acc["platform"], acc["username"], e)
        logger.info("Check done: %d/%d accounts", ok, len(accounts))

    def check_single(self, account_id):
        acc = db.get_account(account_id)
        if not acc:
            return False
        monitor = self._monitors.get(acc["platform"])
        if not monitor:
            return False
        try:
            monitor.check(acc, db)
            return True
        except Exception as e:
            logger.error("Check failed %s/%s: %s", acc["platform"], acc["username"], e)
            return False
