"""
CORAL Availability Checker
========================

Quick check if OSINT CORAL is available for webhook integration.
Falls back to standalone mode if hub is not reachable.
"""

import requests
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def check_coral_available(hub_url: str, timeout: float = 1.0) -> Tuple[bool, str]:
    """
    Quick check if hub is available.

    Args:
        hub_url: CORAL base URL (e.g., http://localhost:3333)
        timeout: Timeout in seconds (default: 1.0 for fast check)

    Returns:
        Tuple of (is_available, message)

    Example:
        available, msg = check_coral_available("http://localhost:3333")
        if available:
            print("CORAL is available, will send webhooks")
        else:
            print(f"CORAL unavailable: {msg}, running standalone")
    """
    try:
        # Try to ping the hub stats endpoint (lightweight)
        response = requests.get(f"{hub_url}/api/stats", timeout=timeout)

        if response.status_code == 200:
            return True, "CORAL is available"
        else:
            return False, f"CORAL returned status {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "CORAL connection timeout"
    except requests.exceptions.ConnectionError:
        return False, "CORAL not reachable"
    except Exception as e:
        return False, f"CORAL check failed: {str(e)}"


def should_use_coral(config, monitor_name: str) -> Tuple[bool, str]:
    """
    Determine if monitor should use hub based on config and availability.

    Args:
        config: Config loader instance
        monitor_name: Name of monitor (instagram, pinterest, spotify)

    Returns:
        Tuple of (use_hub, reason)
    """
    # Check if webhooks are explicitly disabled in config
    if not config.is_webhook_enabled(monitor_name):
        return False, "Webhooks disabled in config"

    # Check if running in standalone mode
    if config.is_monitor_standalone(monitor_name):
        return False, "Standalone mode enabled in config"

    # Get hub URL from config
    hub_url = config.get(f"{monitor_name}.webhook.url", "")
    if not hub_url:
        return False, "No webhook URL configured"

    # Extract base URL (remove /api/webhook/... path)
    try:
        base_url = hub_url.split("/api/")[0]
    except:
        base_url = hub_url

    # Quick check if hub is available
    available, message = check_coral_available(base_url, timeout=0.5)

    if available:
        return True, "CORAL is available and webhooks enabled"
    else:
        return False, f"CORAL not available ({message}), using standalone mode"


def log_mode(monitor_name: str, use_hub: bool, reason: str):
    """Log the operating mode for this monitor"""
    if use_hub:
        logger.info(f"🌐 {monitor_name.title()} Monitor: INTEGRATED mode - {reason}")
    else:
        logger.info(f"🔧 {monitor_name.title()} Monitor: STANDALONE mode - {reason}")
