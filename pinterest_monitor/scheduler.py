from apscheduler.schedulers.background import BackgroundScheduler
from database import get_all_boards, update_pin_count, get_all_users, update_user_activity
from monitor import PinterestMonitor
from config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitorScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.monitor = PinterestMonitor()
        self.check_interval = config.get_int('monitoring', 'check_interval')
        self.is_running = False
    
    def check_all_boards(self):
        """Check all monitored boards for pin count updates"""
        logger.info("Starting scheduled check of all boards...")
        boards = get_all_boards()
        
        # Track which users had activity
        users_with_activity = set()
        
        for board in boards:
            try:
                logger.info(f"Checking board: {board['name']} ({board['url']})")
                pin_count = self.monitor.get_pin_count(board['url'])
                
                if pin_count is not None:
                    old_count = board['current_pin_count']
                    update_pin_count(board['id'], pin_count)
                    
                    if pin_count > old_count:
                        logger.info(f"  📌 New pins detected! {old_count} -> {pin_count} (+{pin_count - old_count})")
                        users_with_activity.add(board['username'])
                    else:
                        logger.info(f"  ✓ No change ({pin_count} pins)")
                else:
                    logger.warning(f"  ✗ Failed to get pin count")
            
            except Exception as e:
                logger.error(f"Error checking board {board['id']}: {e}")
        
        # Update last activity time for users who had new pins
        for username in users_with_activity:
            update_user_activity(username)
            logger.info(f"Updated activity time for user: {username}")
        
        logger.info("Scheduled check completed.")
    
    def check_single_board(self, board_id):
        """Check a single board"""
        from database import get_board
        board = get_board(board_id)
        if not board:
            return False
        
        logger.info(f"Manually checking board: {board['name']}")
        pin_count = self.monitor.get_pin_count(board['url'])
        
        if pin_count is not None:
            old_count = board['current_pin_count']
            update_pin_count(board['id'], pin_count)
            
            # Update user activity if pins changed
            if pin_count > old_count:
                update_user_activity(board['username'])
            
            logger.info(f"  Updated: {pin_count} pins")
            return True
        
        logger.warning(f"  Failed to check board")
        return False
    
    def start(self):
        """Start the background scheduler"""
        if not self.is_running:
            self.scheduler.add_job(
                self.check_all_boards,
                'interval',
                minutes=self.check_interval,
                id='check_all',
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler started. Checking every {self.check_interval} minutes.")
    
    def stop(self):
        """Stop the background scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped.")
    
    def run_now(self):
        """Manually trigger a check"""
        self.check_all_boards()
