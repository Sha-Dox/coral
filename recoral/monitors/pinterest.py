import re
import json
import time
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_DELAY = 1.0
MAX_RETRIES = 2
RETRY_DELAY = 3


def _retry(fn, *args, retries=MAX_RETRIES, **kwargs):
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt == retries:
                raise
            logger.warning("Retry %d/%d: %s", attempt + 1, retries, e)
            time.sleep(RETRY_DELAY * (attempt + 1))


class PinterestMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def get_user_boards(self, username):
        boards = []
        uname_lower = username.lower()
        for domain in ("www.pinterest.com", "tr.pinterest.com", "pinterest.com"):
            try:
                resp = self.session.get(f"https://{domain}/{username}/", timeout=10)
                resp.raise_for_status()
                matches = set(re.findall(r'"(/[^"/]+/[^"/]+/)"', resp.text))
                excluded = {"_created", "_saved", "_pins", "pins", "boards"}
                seen_urls = set()
                for path in matches:
                    parts = path.strip("/").split("/")
                    if len(parts) != 2:
                        continue
                    path_user, slug = parts
                    if path_user.lower() != uname_lower:
                        continue
                    if slug in excluded or slug.startswith("_"):
                        continue
                    board_url = f"https://{domain}{path}"
                    if board_url in seen_urls:
                        continue
                    seen_urls.add(board_url)
                    info = _retry(self.get_board_info, board_url)
                    if info:
                        boards.append(info)
                    time.sleep(REQUEST_DELAY)
                if boards:
                    return boards
            except Exception as e:
                logger.error("boards error %s/%s: %s", domain, username, e)
        return boards

    def get_board_info(self, board_url):
        resp = self.session.get(board_url, timeout=10)
        resp.raise_for_status()
        text = resp.text

        if resp.url.rstrip("/").endswith("pinterest.com") or "<title>Pinterest</title>" in text[:2000]:
            return None

        m = re.search(r'"pin_count":(\d+)', text)
        pin_count = int(m.group(1)) if m else 0

        name = None
        m = re.search(r'<meta property="og:title" content="([^"]+)"', text)
        if m:
            name = m.group(1)
        if not name:
            parts = board_url.rstrip("/").split("/")
            name = parts[-1].replace("-", " ").title() if len(parts) >= 2 else "Unknown"
        name = name.replace("\\u002F", "/").replace("\\", "")

        description = None
        m = re.search(r'<meta property="og:description" content="([^"]*)"', text)
        if m and m.group(1).strip():
            description = m.group(1).strip()

        parts = board_url.rstrip("/").split("/")
        uname = parts[-2] if len(parts) >= 2 else "unknown"

        return {"url": board_url, "name": name, "description": description,
                "username": uname, "pin_count": pin_count}

    def get_user_info(self, username):
        for domain in ("www.pinterest.com", "tr.pinterest.com"):
            try:
                resp = self.session.get(f"https://{domain}/{username}/", timeout=10)
                resp.raise_for_status()
                text = resp.text
                m = re.search(r'"full_name":"([^"]+)"', text)
                display = m.group(1) if m and len(m.group(1)) >= 2 else username

                follower_count = None
                m = re.search(r'"follower_count":(\d+)', text)
                if m:
                    follower_count = int(m.group(1))

                pin_count = None
                m = re.search(r'"pin_count":(\d+)', text)
                if m:
                    pin_count = int(m.group(1))

                return {"username": username, "display_name": display,
                        "followers": follower_count, "pins": pin_count}
            except Exception:
                continue
        return None

    def check(self, account, db):
        username = account["username"]
        account_id = account["id"]
        logger.info("Checking Pinterest: %s", username)

        try:
            user_info = _retry(self.get_user_info, username)
            boards = _retry(self.get_user_boards, username)
        except Exception as e:
            logger.error("Pinterest check failed for %s: %s", username, e)
            db.record_check_error(account_id, str(e))
            return

        if not boards:
            logger.warning("No boards found for %s", username)
            db.record_check_success(account_id, {"boards": [], "user": user_info})
            return

        old = {}
        if account.get("last_data"):
            try:
                old = json.loads(account["last_data"])
            except (json.JSONDecodeError, TypeError):
                pass

        # Diff user-level stats
        from notifier import notify
        old_user = old.get("user") or {}
        if user_info and old_user:
            if old_user.get("followers") is not None and user_info.get("followers") is not None:
                if user_info["followers"] != old_user["followers"]:
                    diff = user_info["followers"] - old_user["followers"]
                    summary = f'Followers: {old_user["followers"]} -> {user_info["followers"]} ({diff:+d})'
                    db.add_event(account_id, "follower_change", summary,
                                 {"old": old_user["followers"], "new": user_info["followers"]})
                    notify(summary, "pinterest", username, "follower_change")

        # Diff boards
        existing = {b["url"]: b for b in db.get_pinterest_boards(account_id)}

        for board in boards:
            url = board["url"]
            pins = board["pin_count"]

            if url in existing:
                old_board = existing[url]
                db.update_pinterest_board(old_board["id"], pins, board["name"], board.get("description"))
                if pins > old_board["current_pin_count"]:
                    diff = pins - old_board["current_pin_count"]
                    summary = f'+{diff} pin(s) on "{board["name"]}" ({old_board["current_pin_count"]} -> {pins})'
                    db.add_event(account_id, "new_pins", summary,
                                 {"board_name": board["name"], "board_url": url,
                                  "old_count": old_board["current_pin_count"], "new_count": pins})
                    notify(summary, "pinterest", username, "new_pins")
                if board.get("description") and old_board.get("description") and board["description"] != old_board["description"]:
                    summary = f'Board "{board["name"]}" description changed'
                    db.add_event(account_id, "board_update", summary,
                                 {"board_name": board["name"], "old_desc": old_board["description"],
                                  "new_desc": board["description"]})
                    notify(summary, "pinterest", username, "board_update")
            else:
                db.add_pinterest_board(account_id, url, board["name"], pins, board.get("description"))
                summary = f'New board: "{board["name"]}" ({pins} pins)'
                db.add_event(account_id, "new_board", summary,
                             {"board_name": board["name"], "board_url": url, "pin_count": pins})
                notify(summary, "pinterest", username, "new_board")

        db.record_check_success(account_id, {"boards": boards, "user": user_info})
        logger.info("  Pinterest done: %s (%d boards)", username, len(boards))
