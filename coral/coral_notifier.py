#!/usr/bin/env python3
"""
Hub Notifier - Integration Helper for OSINT Monitors
====================================================

This module provides an easy way for monitors to send events to the CORAL.
It automatically detects if the hub is available and falls back to standalone mode.

Usage Example:
    from coral_notifier import CoralNotifier
    
    # Initialize (auto-detects hub from config.yaml)
    notifier = CoralNotifier('instagram')
    
    # Send events (only if hub available)
    notifier.send_event(
        username='user123',
        event_type='new_post',
        summary='Posted a new photo',
        data={'post_id': '123'}
    )
"""

import requests
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config_loader import config
    from coral_checker import should_use_coral, log_mode

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


class CoralNotifier:
    """Helper class to send events to CORAL with auto-detection"""

    def __init__(
        self,
        platform: str,
        hub_url: Optional[str] = None,
        secret: Optional[str] = None,
        auto_detect: bool = True,
    ):
        """Initialize notifier with auto-detection"""
        self.platform = platform.lower()
        self._hub_available = False
        self._hub_url = None
        self._secret = None

        # Try to auto-detect from config
        if auto_detect and CONFIG_AVAILABLE:
            use_hub, reason = should_use_coral(config, self.platform)
            self._hub_available = use_hub

            if use_hub:
                self._hub_url = hub_url or config.get(f"{self.platform}.webhook.url")
                self._secret = secret or config.get(
                    f"{self.platform}.webhook.secret", ""
                )

            log_mode(self.platform, use_hub, reason)
        elif hub_url:
            # Manual mode
            self._hub_url = hub_url
            self._secret = secret or ""
            self._hub_available = True
            logger.info(f"🌐 {platform.title()} Monitor: INTEGRATED mode (manual)")
        else:
            logger.info(f"🔧 {platform.title()} Monitor: STANDALONE mode")

    def is_hub_mode(self) -> bool:
        """Check if running in hub mode"""
        return self._hub_available

    def get_mode_string(self) -> str:
        """Get human-readable mode string"""
        return "INTEGRATED" if self._hub_available else "STANDALONE"

    def send_event(
        self,
        username: str,
        event_type: str,
        summary: str,
        event_time: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send event to hub (only if available)"""
        if not self._hub_available:
            logger.debug(f"Standalone mode: Skipping hub notification")
            return True

        try:
            payload = {
                "username": username,
                "event_type": event_type,
                "summary": summary,
                "event_time": event_time or datetime.utcnow().isoformat(),
                "data": data or {},
            }

            headers = {"Content-Type": "application/json"}
            if self._secret:
                headers["X-Webhook-Secret"] = self._secret

            response = requests.post(
                self._hub_url, json=payload, headers=headers, timeout=5
            )

            if response.status_code == 200:
                logger.debug(f"Event sent to hub: {username}/{event_type}")
                return True
            else:
                logger.warning(f"Hub returned {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to send event to hub: {e}")
            return False

    def send_post_event(
        self,
        username: str,
        caption: str = "",
        post_url: str = "",
        post_id: str = "",
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Send a new post event"""
        return self.send_event(
            username=username,
            event_type="new_post",
            summary=f"New post: {caption[:50]}..." if caption else "New post",
            event_time=timestamp.isoformat() if timestamp else None,
            data={"caption": caption, "url": post_url, "post_id": post_id},
        )

    def send_bio_change(self, username: str, old_bio: str, new_bio: str) -> bool:
        """Send a bio change event"""
        return self.send_event(
            username=username,
            event_type="bio_change",
            summary="Bio updated",
            data={"old_bio": old_bio, "new_bio": new_bio},
        )

    def send_follower_change(
        self, username: str, old_count: int, new_count: int
    ) -> bool:
        """Send a follower count change event"""
        diff = new_count - old_count
        return self.send_event(
            username=username,
            event_type="follower_change",
            summary=f"Followers: {old_count} → {new_count} ({diff:+d})",
            data={"old_count": old_count, "new_count": new_count, "difference": diff},
        )
