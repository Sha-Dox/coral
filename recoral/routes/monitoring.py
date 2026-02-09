from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
import database as db
from maigret_search import MAIGRET_AVAILABLE

bp = Blueprint("monitoring", __name__, url_prefix="/api")


@bp.route("/check-all", methods=["POST"])
def check_all():
    scheduler = current_app.config.get("scheduler")
    if not scheduler:
        return jsonify({"success": False, "error": "Scheduler not initialized"}), 500
    import threading
    threading.Thread(target=scheduler.check_all, daemon=True).start()
    return jsonify({"success": True, "message": "Check started"})


@bp.route("/check/<int:account_id>", methods=["POST"])
def check_single(account_id):
    scheduler = current_app.config.get("scheduler")
    if not scheduler:
        return jsonify({"success": False, "error": "Scheduler not initialized"}), 500
    import threading
    threading.Thread(target=scheduler.check_single, args=(account_id,), daemon=True).start()
    return jsonify({"success": True, "message": "Check started"})


@bp.route("/stats", methods=["GET"])
def stats():
    identities = db.get_all_identities()
    total_accounts = sum(len(i["accounts"]) for i in identities)
    events = db.get_events(limit=1000)
    now = datetime.now(timezone.utc)
    recent = 0
    for e in events:
        if e.get("created_at"):
            try:
                from dateutil import parser as dp
                dt = dp.parse(e["created_at"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if (now - dt).total_seconds() < 86400:
                    recent += 1
            except (ValueError, TypeError):
                pass

    return jsonify({
        "success": True,
        "stats": {
            "identities": len(identities),
            "accounts": total_accounts,
            "recent_events": recent,
        },
    })


@bp.route("/maigret/search", methods=["POST"])
def maigret_search():
    if not MAIGRET_AVAILABLE:
        return jsonify({"success": False, "error": "Maigret not available"}), 503

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"success": False, "error": "Username is required"}), 400

    from maigret_search import search

    top_sites = max(1, min(int(data.get("top_sites", 500)), 5000))
    if data.get("all_sites"):
        top_sites = 999999999
    timeout = max(1, min(int(data.get("timeout", 5)), 60))
    max_connections = max(1, min(int(data.get("max_connections", 50)), 200))
    retries = max(0, min(int(data.get("retries", 0)), 5))
    id_type = (data.get("id_type") or "username").strip()

    tags = _parse_list(data.get("tags"))
    site_list = _parse_list(data.get("site_list"))

    cookies_file = None
    if data.get("use_cookies"):
        for c in [Path("cookies.txt"), Path(__file__).resolve().parent.parent / "maigret" / "cookies.txt"]:
            if c.exists():
                cookies_file = c
                break

    start = datetime.utcnow()
    try:
        results, scope = search(
            username, top_sites, timeout, max_connections, retries,
            id_type, tags, site_list,
            bool(data.get("include_disabled")), bool(data.get("check_domains")),
            cookies_file,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    found = []
    for site_name, site_data in results.items():
        status = site_data.get("status")
        if not status or not status.is_found():
            continue
        found.append({
            "site_name": site_name,
            "url": site_data.get("url_user") or getattr(status, "site_url_user", ""),
            "status": str(getattr(status, "status", "Unknown")),
            "tags": getattr(status, "tags", []),
        })
    found.sort(key=lambda x: x["site_name"].lower())
    duration = int((datetime.utcnow() - start).total_seconds() * 1000)

    return jsonify({
        "success": True, "username": username,
        "stats": {"checked_sites": len(results), "scope_sites": scope,
                  "found_sites": len(found), "duration_ms": duration},
        "found": found,
    })


@bp.route("/maigret/link", methods=["POST"])
def maigret_link():
    """Link a found profile from maigret search to an identity as an account."""
    data = request.get_json() or {}
    identity_id = data.get("identity_id")
    platform = (data.get("platform") or "").strip().lower()
    username = (data.get("username") or "").strip()

    if not identity_id or not platform or not username:
        return jsonify({"success": False, "error": "identity_id, platform, and username are required"}), 400
    if platform not in ("instagram", "pinterest", "spotify"):
        return jsonify({"success": False, "error": f"Unsupported platform: {platform}"}), 400

    identity = db.get_identity(identity_id)
    if not identity:
        return jsonify({"success": False, "error": "Identity not found"}), 404

    account_id = db.add_account(identity_id, platform, username)
    if not account_id:
        return jsonify({"success": False, "error": "Account already exists"}), 409

    return jsonify({"success": True, "id": account_id}), 201


def _parse_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.replace("\n", ",").split(",") if v.strip()]
    return []
