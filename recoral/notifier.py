"""Notification system for CORAL. Sends alerts via Discord webhooks and ntfy.sh."""
import json
import logging
import requests

logger = logging.getLogger(__name__)

TIMEOUT = 10


def _get_config():
    import database as db
    return {
        "discord_webhook": db.get_setting("discord_webhook", ""),
        "ntfy_topic": db.get_setting("ntfy_topic", ""),
        "ntfy_server": db.get_setting("ntfy_server", "https://ntfy.sh"),
        "notifications_enabled": db.get_setting("notifications_enabled", "true"),
    }


def notify(summary, platform=None, username=None, event_type=None, event_data=None):
    """Send a notification for a detected event."""
    cfg = _get_config()
    if cfg["notifications_enabled"] != "true":
        return

    sent = False
    if cfg["discord_webhook"]:
        sent = _send_discord(cfg["discord_webhook"], summary, platform, username, event_type) or sent
    if cfg["ntfy_topic"]:
        sent = _send_ntfy(cfg["ntfy_server"], cfg["ntfy_topic"], summary, platform, username) or sent

    return sent


def _send_discord(webhook_url, summary, platform=None, username=None, event_type=None):
    platform_colors = {"instagram": 0xE1306C, "pinterest": 0xE60023, "spotify": 0x1DB954}
    platform_emoji = {"instagram": ":camera:", "pinterest": ":pushpin:", "spotify": ":musical_note:"}

    color = platform_colors.get(platform, 0x6366F1)
    emoji = platform_emoji.get(platform, ":bell:")

    embed = {
        "color": color,
        "description": summary,
        "footer": {"text": "CORAL"},
    }
    if username:
        title = f"{emoji} @{username}"
        if platform:
            title += f" ({platform})"
        embed["title"] = title

    try:
        resp = requests.post(
            webhook_url,
            json={"embeds": [embed]},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Discord notification failed: %s", e)
        return False


def _send_ntfy(server, topic, summary, platform=None, username=None):
    title = "CORAL"
    if username and platform:
        title = f"@{username} ({platform})"
    elif username:
        title = f"@{username}"

    tags = ["coral"]
    if platform:
        tags.append(platform)

    try:
        resp = requests.post(
            f"{server.rstrip('/')}/{topic}",
            data=summary.encode("utf-8"),
            headers={
                "Title": title,
                "Tags": ",".join(tags),
                "Priority": "default",
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("ntfy notification failed: %s", e)
        return False


def test_notification():
    """Send a test notification to verify configuration."""
    cfg = _get_config()
    results = {}

    if cfg["discord_webhook"]:
        results["discord"] = _send_discord(
            cfg["discord_webhook"], "Test notification from CORAL", "coral", "test"
        )
    else:
        results["discord"] = None

    if cfg["ntfy_topic"]:
        results["ntfy"] = _send_ntfy(
            cfg["ntfy_server"], cfg["ntfy_topic"], "Test notification from CORAL"
        )
    else:
        results["ntfy"] = None

    return results
