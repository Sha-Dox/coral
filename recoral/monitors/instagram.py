import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import instaloader
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
    logger.warning("instaloader not installed - Instagram monitoring unavailable")


class InstagramMonitor:
    def __init__(self):
        if not AVAILABLE:
            return
        self._loaders = {}

    def _get_loader(self, session_username=None):
        if not AVAILABLE:
            raise RuntimeError("instaloader not available")
        if session_username in self._loaders:
            return self._loaders[session_username]
        loader = instaloader.Instaloader()
        if session_username:
            try:
                loader.load_session_from_file(session_username)
                logger.info("Instagram session loaded for %s", session_username)
            except Exception as e:
                logger.warning("Failed to load Instagram session for %s: %s", session_username, e)
        self._loaders[session_username] = loader
        return loader

    def _resolve_session(self, account):
        config = {}
        if account.get("config_json"):
            try:
                config = json.loads(account["config_json"])
            except (json.JSONDecodeError, TypeError):
                pass

        session_username = config.get("session_username", "")
        if not session_username:
            import database as _db
            session_username = _db.get_setting("instagram_session", "")
        if not session_username:
            import config as app_config
            session_username = app_config.INSTAGRAM_SESSION_FILE or None
        return session_username

    def get_profile(self, username, session_username=None):
        loader = self._get_loader(session_username)
        p = instaloader.Profile.from_username(loader.context, username)
        return {
            "followers": p.followers,
            "followings": p.followees,
            "posts": p.mediacount,
            "bio": p.biography,
            "is_private": p.is_private,
            "full_name": p.full_name,
        }

    def check(self, account, db):
        if not AVAILABLE:
            return

        username = account["username"]
        account_id = account["id"]
        logger.info("Checking Instagram: %s", username)

        session_username = self._resolve_session(account)

        try:
            data = self.get_profile(username, session_username)
        except instaloader.exceptions.LoginRequiredException:
            msg = "Session expired or login required"
            logger.error("Instagram %s: %s", username, msg)
            db.record_check_error(account_id, msg)
            from notifier import notify
            notify(f"Instagram session expired for @{username}. Re-run: instaloader --login {session_username or 'USERNAME'}",
                   "instagram", username, "session_expired")
            return
        except instaloader.exceptions.ConnectionException as e:
            if "429" in str(e) or "rate" in str(e).lower():
                msg = "Rate limited by Instagram"
            elif "401" in str(e):
                msg = "Session expired or unauthorized"
            else:
                msg = str(e)
            logger.error("Instagram %s: %s", username, msg)
            db.record_check_error(account_id, msg)
            return
        except Exception as e:
            logger.error("Instagram fetch failed for %s: %s", username, e)
            db.record_check_error(account_id, str(e))
            return

        old = {}
        if account.get("last_data"):
            try:
                old = json.loads(account["last_data"])
            except (json.JSONDecodeError, TypeError):
                pass

        from notifier import notify

        if old:
            if old.get("followers") is not None and data["followers"] != old["followers"]:
                diff = data["followers"] - old["followers"]
                summary = f'Followers: {old["followers"]} -> {data["followers"]} ({diff:+d})'
                db.add_event(account_id, "follower_change", summary,
                             {"old": old["followers"], "new": data["followers"]})
                notify(summary, "instagram", username, "follower_change")

            if old.get("followings") is not None and data["followings"] != old["followings"]:
                diff = data["followings"] - old["followings"]
                summary = f'Following: {old["followings"]} -> {data["followings"]} ({diff:+d})'
                db.add_event(account_id, "following_change", summary,
                             {"old": old["followings"], "new": data["followings"]})
                notify(summary, "instagram", username, "following_change")

            if old.get("bio") is not None and data["bio"] != old["bio"]:
                summary = "Bio updated"
                db.add_event(account_id, "bio_change", summary,
                             {"old_bio": old["bio"], "new_bio": data["bio"]})
                notify(summary, "instagram", username, "bio_change")

            if old.get("posts") is not None and data["posts"] > old["posts"]:
                diff = data["posts"] - old["posts"]
                summary = f'{diff} new post(s) ({old["posts"]} -> {data["posts"]})'
                db.add_event(account_id, "new_post", summary,
                             {"old": old["posts"], "new": data["posts"]})
                notify(summary, "instagram", username, "new_post")

            if old.get("full_name") and data["full_name"] != old["full_name"]:
                summary = f'Name changed: "{old["full_name"]}" -> "{data["full_name"]}"'
                db.add_event(account_id, "name_change", summary,
                             {"old": old["full_name"], "new": data["full_name"]})
                notify(summary, "instagram", username, "name_change")

            if old.get("is_private") is not None and data["is_private"] != old["is_private"]:
                status = "private" if data["is_private"] else "public"
                summary = f"Account is now {status}"
                db.add_event(account_id, "privacy_change", summary,
                             {"old": old["is_private"], "new": data["is_private"]})
                notify(summary, "instagram", username, "privacy_change")

        db.record_check_success(account_id, data)
        logger.info("  Instagram done: %s (%d followers, %d posts)", username, data["followers"], data["posts"])
