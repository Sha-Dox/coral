"""Extract Instagram/Spotify session cookies from Chrome/Firefox and create instaloader session files."""

import json
import logging
import os
import pickle
import shutil
import sqlite3
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from pycookiecheat import chrome_cookies as _pycookiecheat
    PYCOOKIECHEAT = True
except ImportError:
    PYCOOKIECHEAT = False

# Cache Chrome Safe Storage password so Keychain only prompts once per app run
_chrome_password_cache = None


def extract_instagram_session(browser="chrome"):
    """Extract Instagram sessionid from a browser and create an instaloader session.

    Returns dict with keys: success, username, session_file, error
    """
    try:
        if browser == "chrome":
            cookies = _get_chrome_cookies()
        elif browser == "firefox":
            cookies = _get_firefox_cookies()
        else:
            return {"success": False, "error": f"Unsupported browser: {browser}"}
    except Exception as e:
        logger.error("Failed to extract cookies from %s: %s", browser, e)
        return {"success": False, "error": str(e)}

    sessionid = None
    for c in cookies:
        if c["name"] == "sessionid" and c["value"]:
            sessionid = c["value"]
            break

    if not sessionid:
        return {"success": False, "error": f"No Instagram session found in {browser}. Make sure you're logged into instagram.com."}

    # Try to figure out the username
    username = None
    try:
        username = _get_ig_username(sessionid)
    except Exception as e:
        logger.warning("Couldn't auto-detect IG username: %s", e)

    # If we couldn't detect username, try to extract numeric user ID from sessionid
    if not username:
        # sessionid format: "{user_id}%3A..."
        if "%3A" in sessionid:
            candidate = sessionid.split("%3A")[0]
            if candidate.isdigit():
                username = candidate
        if not username:
            username = "imported"

    # Create instaloader session file
    try:
        session_file = _create_instaloader_session(username, cookies)
    except Exception as e:
        return {"success": False, "error": f"Failed to create session file: {e}"}

    return {
        "success": True,
        "username": username,
        "session_file": str(session_file),
        "browser": browser,
        "needs_username": username.isdigit() or username == "imported",
    }


def _get_ig_username(sessionid):
    """Query Instagram to get the username for a sessionid."""
    import requests

    # Clean the sessionid - strip any non-ASCII or control chars from decryption artifacts
    sessionid = sessionid.strip().strip("\x00")
    sessionid = "".join(c for c in sessionid if ord(c) < 128 and c.isprintable())

    session = requests.Session()
    session.cookies.set("sessionid", sessionid, domain=".instagram.com")
    resp = session.get(
        "https://www.instagram.com/api/v1/users/web_profile_info/?username=instagram",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/",
        },
        timeout=10,
    )

    # If that works, we know the session is valid. Now get our own username.
    # Parse ds_user_id from sessionid or check the session cookies
    resp2 = session.get(
        "https://www.instagram.com/accounts/edit/?__a=1&__d=dis",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/edit/",
        },
        timeout=10,
    )

    # Try parsing username from response
    try:
        data = resp2.json()
        if "form_data" in data:
            return data["form_data"]["username"]
        if "user" in data:
            return data["user"]["username"]
    except Exception:
        pass

    # Fallback: extract ds_user_id from sessionid cookie format or page
    # sessionid format is often "{user_id}%3A..."
    if "%3A" in sessionid:
        user_id = sessionid.split("%3A")[0]
        try:
            resp3 = session.get(
                f"https://www.instagram.com/api/v1/users/{user_id}/info/",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "X-IG-App-ID": "936619743392459",
                },
                timeout=10,
            )
            data = resp3.json()
            return data["user"]["username"]
        except Exception:
            pass

    raise RuntimeError("Session is valid but couldn't determine username. Set it manually in the field above.")


def _create_instaloader_session(username, cookies):
    """Create an instaloader-compatible session file from browser cookies."""
    # Instaloader expects a pickled plain dict, NOT a RequestsCookieJar
    cookie_dict = {c["name"]: c["value"] for c in cookies}

    session_dir = Path.home() / ".config" / "instaloader"
    session_dir.mkdir(parents=True, exist_ok=True)
    session_file = session_dir / f"session-{username}"

    with open(session_file, "wb") as f:
        pickle.dump(cookie_dict, f)

    logger.info("Created instaloader session: %s", session_file)
    return session_file


def extract_spotify_cookie(browser="chrome"):
    """Extract sp_dc cookie from Chrome or Firefox.

    Returns dict with keys: success, sp_dc, error
    """
    try:
        if browser == "chrome":
            cookies = _get_chrome_cookies_for("spotify.com")
        elif browser == "firefox":
            cookies = _get_firefox_cookies_for("spotify.com")
        else:
            return {"success": False, "error": f"Unsupported browser: {browser}"}
    except Exception as e:
        logger.error("Failed to extract cookies from %s: %s", browser, e)
        return {"success": False, "error": str(e)}

    sp_dc = None
    for c in cookies:
        if c["name"] == "sp_dc" and c["value"]:
            sp_dc = c["value"]
            break

    if not sp_dc:
        return {"success": False, "error": f"No sp_dc cookie found in {browser}. Log into open.spotify.com first."}

    return {"success": True, "sp_dc": sp_dc, "browser": browser}


# ---- Chrome (macOS) ----

def _get_chrome_cookies(domain="instagram.com"):
    """Extract cookies for a domain from Chrome on macOS."""
    return _get_chrome_cookies_for(domain)


def _get_chrome_password():
    """Get Chrome Safe Storage password from Keychain, cached after first call."""
    global _chrome_password_cache
    if _chrome_password_cache is not None:
        return _chrome_password_cache

    import subprocess
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "Chrome Safe Storage", "-w"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Could not get Chrome Safe Storage key from Keychain.")
    _chrome_password_cache = result.stdout.strip()
    return _chrome_password_cache


def _get_chrome_cookies_for(domain):
    """Extract cookies for a domain from Chrome using pycookiecheat."""
    if not PYCOOKIECHEAT:
        raise RuntimeError("pycookiecheat not installed. Run: pip install pycookiecheat")

    chrome_dir = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    if not chrome_dir.exists():
        raise FileNotFoundError("Chrome not found. Is Chrome installed?")

    cookie_file = None
    for profile in ["Default", "Profile 1", "Profile 2", "Profile 3", "Guest Profile"]:
        candidate = chrome_dir / profile / "Cookies"
        if candidate.exists():
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
            tmp.close()
            try:
                shutil.copy2(candidate, tmp.name)
                conn = sqlite3.connect(tmp.name)
                count = conn.execute(
                    "SELECT COUNT(*) FROM cookies WHERE host_key LIKE ?",
                    (f"%{domain}%",)
                ).fetchone()[0]
                conn.close()
            finally:
                os.unlink(tmp.name)
            if count > 0:
                cookie_file = candidate
                break

    if not cookie_file:
        raise FileNotFoundError(f"No Chrome profile has cookies for {domain}.")

    password = _get_chrome_password()
    url = f"https://www.{domain}"
    cookie_dict = _pycookiecheat(url, cookie_file=str(cookie_file), password=password)

    cookies = []
    for name, value in cookie_dict.items():
        cookies.append({"name": name, "value": value, "domain": f".{domain}", "path": "/"})

    return cookies


# ---- Firefox ----

def _get_firefox_cookies(domain="instagram.com"):
    """Extract cookies for a domain from Firefox on macOS."""
    return _get_firefox_cookies_for(domain)


def _get_firefox_cookies_for(domain):
    """Extract cookies for a domain from Firefox on macOS."""
    firefox_dir = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
    if not firefox_dir.exists():
        raise FileNotFoundError("Firefox profiles directory not found. Is Firefox installed?")

    cookie_db = None
    for profile_dir in firefox_dir.iterdir():
        candidate = profile_dir / "cookies.sqlite"
        if candidate.exists():
            cookie_db = candidate
            break

    if not cookie_db:
        raise FileNotFoundError("No Firefox cookie database found.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    try:
        shutil.copy2(cookie_db, tmp.name)
        conn = sqlite3.connect(tmp.name)
        cursor = conn.execute(
            "SELECT name, value, host, path FROM moz_cookies "
            "WHERE host LIKE ?", (f"%{domain}%",)
        )
        cookies = []
        for name, value, host, path in cursor.fetchall():
            cookies.append({"name": name, "value": value, "domain": host, "path": path})
        conn.close()
    finally:
        os.unlink(tmp.name)

    return cookies
