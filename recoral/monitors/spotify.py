import json
import logging
import time
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

TOKEN_URL = "https://open.spotify.com/api/token"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 15
MAX_RETRIES = 2
RETRY_DELAY = 3


class SpotifyMonitor:
    def __init__(self):
        self.session = requests.Session()
        self._tokens = {}  # per sp_dc token cache

    def get_access_token(self, sp_dc):
        cached = self._tokens.get(sp_dc)
        if cached and time.time() < cached["expires"]:
            return cached["token"], cached["client_id"]

        headers = {
            "User-Agent": USER_AGENT, "Accept": "application/json",
            "Referer": "https://open.spotify.com/", "App-Platform": "WebPlayer",
            "Cookie": f"sp_dc={sp_dc}",
        }
        for reason in ("transport", "init"):
            try:
                resp = self.session.get(TOKEN_URL, params={"reason": reason, "productType": "web-player"},
                                        headers=headers, timeout=TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
                token = data.get("accessToken", "")
                if token:
                    client_id = data.get("clientId", "")
                    self._tokens[sp_dc] = {
                        "token": token,
                        "client_id": client_id,
                        "expires": data.get("accessTokenExpirationTimestampMs", 0) / 1000,
                    }
                    return token, client_id
            except Exception as e:
                logger.warning("Token request failed (reason=%s): %s", reason, e)
        raise RuntimeError("Failed to obtain Spotify access token - sp_dc cookie may be expired")

    def _headers(self, token, client_id=""):
        h = {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}
        if client_id:
            h["Client-Id"] = client_id
        return h

    def get_user_info(self, token, client_id, user_id):
        url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{user_id}?playlist_limit=0&artist_limit=0&episode_limit=0&market=from_token"
        resp = self.session.get(url, headers=self._headers(token, client_id), timeout=TIMEOUT)
        resp.raise_for_status()
        d = resp.json()
        return {
            "display_name": d.get("name", ""),
            "followers": d.get("followers_count", 0),
            "followings": d.get("following_count", 0),
            "image_url": d.get("image_url", ""),
        }

    def _get_profiles(self, token, client_id, user_id, endpoint):
        url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{user_id}/{endpoint}?market=from_token"
        try:
            resp = self.session.get(url, headers=self._headers(token, client_id), timeout=TIMEOUT)
            resp.raise_for_status()
            profiles = resp.json().get("profiles") or []
            return [{"name": p.get("name"), "uri": p.get("uri")} for p in profiles if isinstance(p, dict)]
        except Exception as e:
            logger.error("Failed to get %s for %s: %s", endpoint, user_id, e)
            return []

    def get_user_followers(self, token, client_id, user_id):
        return self._get_profiles(token, client_id, user_id, "followers")

    def get_user_followings(self, token, client_id, user_id):
        return self._get_profiles(token, client_id, user_id, "following")

    def get_public_playlists(self, token, client_id, user_id):
        url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{user_id}?playlist_limit=50&artist_limit=0&episode_limit=0&market=from_token"
        try:
            resp = self.session.get(url, headers=self._headers(token, client_id), timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            playlists = data.get("public_playlists") or []
            return [{"name": p.get("name", ""), "uri": p.get("uri", ""),
                      "followers": p.get("followers_count", 0)} for p in playlists if isinstance(p, dict)]
        except Exception as e:
            logger.error("Failed to get playlists for %s: %s", user_id, e)
            return []

    def _resolve_sp_dc(self, account):
        config = {}
        if account.get("config_json"):
            try:
                config = json.loads(account["config_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        sp_dc = config.get("sp_dc", "")
        if not sp_dc:
            import database as _db
            sp_dc = _db.get_setting("sp_dc_cookie", "")
        if not sp_dc:
            import config as app_config
            sp_dc = app_config.SP_DC_COOKIE
        return sp_dc

    def check(self, account, db):
        username = account["username"]
        account_id = account["id"]

        sp_dc = self._resolve_sp_dc(account)
        if not sp_dc:
            logger.warning("No sp_dc cookie for Spotify target %s", username)
            db.record_check_error(account_id, "No sp_dc cookie configured")
            return

        logger.info("Checking Spotify: %s", username)

        try:
            token, client_id = self.get_access_token(sp_dc)
        except Exception as e:
            logger.error("Spotify token error: %s", e)
            db.record_check_error(account_id, str(e))
            from notifier import notify
            notify(f"Spotify auth failed for @{username}: sp_dc cookie may be expired",
                   "spotify", username, "auth_failed")
            return

        try:
            profile = self.get_user_info(token, client_id, username)
        except Exception as e:
            logger.error("Spotify profile error for %s: %s", username, e)
            db.record_check_error(account_id, str(e))
            return

        current = dict(profile)
        try:
            current["follower_list"] = self.get_user_followers(token, client_id, username)
        except Exception:
            pass
        try:
            current["following_list"] = self.get_user_followings(token, client_id, username)
        except Exception:
            pass
        try:
            current["playlists"] = self.get_public_playlists(token, client_id, username)
        except Exception:
            pass

        old = {}
        if account.get("last_data"):
            try:
                old = json.loads(account["last_data"])
            except (json.JSONDecodeError, TypeError):
                pass

        from notifier import notify

        if old:
            self._diff_counts(db, notify, account_id, username, old, current, "followers", "follower_change", "Followers")
            self._diff_counts(db, notify, account_id, username, old, current, "followings", "following_change", "Following")

            if old.get("display_name") and current["display_name"] != old["display_name"]:
                summary = f'Name: "{old["display_name"]}" -> "{current["display_name"]}"'
                db.add_event(account_id, "name_change", summary,
                             {"old": old["display_name"], "new": current["display_name"]})
                notify(summary, "spotify", username, "name_change")

            self._diff_list(db, notify, account_id, username, old, current, "follower_list",
                            "new_follower", "lost_follower", "New follower(s)", "Lost follower(s)")
            self._diff_list(db, notify, account_id, username, old, current, "following_list",
                            "new_following", "unfollowed", "Now following", "Unfollowed")

            # Playlist diffs
            if "playlists" in old and "playlists" in current:
                old_uris = {p["uri"] for p in old["playlists"] if isinstance(p, dict) and p.get("uri")}
                new_uris = {p["uri"] for p in current["playlists"] if isinstance(p, dict) and p.get("uri")}
                added = new_uris - old_uris
                removed = old_uris - new_uris
                if added:
                    names = [p["name"] for p in current["playlists"] if p.get("uri") in added]
                    summary = f'New playlist(s): {", ".join(names)}'
                    db.add_event(account_id, "new_playlist", summary, {"names": names})
                    notify(summary, "spotify", username, "new_playlist")
                if removed:
                    names = [p["name"] for p in old["playlists"] if p.get("uri") in removed]
                    summary = f'Removed playlist(s): {", ".join(names)}'
                    db.add_event(account_id, "removed_playlist", summary, {"names": names})
                    notify(summary, "spotify", username, "removed_playlist")

        db.record_check_success(account_id, current)
        logger.info("  Spotify done: %s (%s followers)", username, current.get("followers", "?"))

    def _diff_counts(self, db, notify, account_id, username, old, new, key, event_type, label):
        if key in old and old[key] is not None and new.get(key) != old[key]:
            diff = new[key] - old[key]
            summary = f'{label}: {old[key]} -> {new[key]} ({diff:+d})'
            db.add_event(account_id, event_type, summary, {"old": old[key], "new": new[key]})
            notify(summary, "spotify", username, event_type)

    def _diff_list(self, db, notify, account_id, username, old, new, key, add_type, remove_type, add_label, remove_label):
        if key not in old or key not in new:
            return
        old_uris = {f["uri"] for f in old[key] if isinstance(f, dict) and f.get("uri")}
        new_uris = {f["uri"] for f in new[key] if isinstance(f, dict) and f.get("uri")}
        added = new_uris - old_uris
        removed = old_uris - new_uris
        if added:
            names = [f.get("name", "?") for f in new[key] if isinstance(f, dict) and f.get("uri") in added]
            summary = f'{add_label}: {", ".join(names)}'
            db.add_event(account_id, add_type, summary, {"names": names})
            notify(summary, "spotify", username, add_type)
        if removed:
            names = [f.get("name", "?") for f in old[key] if isinstance(f, dict) and f.get("uri") in removed]
            summary = f'{remove_label}: {", ".join(names)}'
            db.add_event(account_id, remove_type, summary, {"names": names})
            notify(summary, "spotify", username, remove_type)
