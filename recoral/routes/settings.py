from flask import Blueprint, request, jsonify, current_app
import config
import database as db

bp = Blueprint("settings", __name__, url_prefix="/api/settings")

ALLOWED_KEYS = {
    "check_interval", "sp_dc_cookie", "instagram_session",
    "discord_webhook", "ntfy_topic", "ntfy_server", "notifications_enabled",
}


@bp.route("", methods=["GET"])
def get_settings():
    saved = db.get_all_settings()
    return jsonify({
        "success": True,
        "settings": {
            "check_interval": saved.get("check_interval", str(config.CHECK_INTERVAL)),
            "sp_dc_cookie": saved.get("sp_dc_cookie", config.SP_DC_COOKIE),
            "instagram_session": saved.get("instagram_session", config.INSTAGRAM_SESSION_FILE),
            "discord_webhook": saved.get("discord_webhook", ""),
            "ntfy_topic": saved.get("ntfy_topic", ""),
            "ntfy_server": saved.get("ntfy_server", "https://ntfy.sh"),
            "notifications_enabled": saved.get("notifications_enabled", "true"),
        },
        "info": {
            "port": config.PORT,
            "host": config.HOST,
            "debug": config.DEBUG,
            "database": config.DATABASE_NAME,
        },
    })


@bp.route("", methods=["PUT"])
def update_settings():
    data = request.get_json() or {}
    updated = []
    for key in ALLOWED_KEYS:
        if key in data:
            val = str(data[key]).strip()
            db.set_setting(key, val)
            updated.append(key)

    if "instagram_session" in updated:
        new_username = str(data["instagram_session"]).strip()
        if new_username:
            from pathlib import Path
            session_dir = Path.home() / ".config" / "instaloader"
            # Rename any numeric/imported session file to the real username
            for old_name in session_dir.glob("session-*"):
                stem = old_name.name.replace("session-", "")
                if stem.isdigit() or stem == "imported":
                    new_path = session_dir / f"session-{new_username}"
                    if not new_path.exists():
                        old_name.rename(new_path)
                    break

    if "check_interval" in updated:
        try:
            new_interval = max(30, int(data["check_interval"]))
            scheduler = current_app.config.get("scheduler")
            if scheduler and scheduler.is_running:
                scheduler.scheduler.reschedule_job("check_all", trigger="interval", seconds=new_interval)
                scheduler.check_interval = new_interval
        except (ValueError, TypeError):
            pass

    return jsonify({"success": True, "updated": updated})


@bp.route("/test-notification", methods=["POST"])
def test_notification():
    from notifier import test_notification
    results = test_notification()
    return jsonify({"success": True, "results": results})


@bp.route("/import-ig-session", methods=["POST"])
def import_ig_session():
    """Import Instagram session from Chrome or Firefox cookies."""
    data = request.get_json() or {}
    browser = data.get("browser", "chrome").lower()
    if browser not in ("chrome", "firefox"):
        return jsonify({"success": False, "error": "Browser must be 'chrome' or 'firefox'"}), 400

    from browser_cookies import extract_instagram_session
    result = extract_instagram_session(browser)

    if result["success"]:
        if not result.get("needs_username"):
            db.set_setting("instagram_session", result["username"])

    return jsonify(result)


@bp.route("/import-spotify-cookie", methods=["POST"])
def import_spotify_cookie():
    """Import Spotify sp_dc cookie from Chrome or Firefox."""
    data = request.get_json() or {}
    browser = data.get("browser", "chrome").lower()
    if browser not in ("chrome", "firefox"):
        return jsonify({"success": False, "error": "Browser must be 'chrome' or 'firefox'"}), 400

    from browser_cookies import extract_spotify_cookie
    result = extract_spotify_cookie(browser)

    if result["success"]:
        db.set_setting("sp_dc_cookie", result["sp_dc"])

    return jsonify(result)
