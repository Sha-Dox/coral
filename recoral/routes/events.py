import json
from flask import Blueprint, request, jsonify
import database as db

bp = Blueprint("events", __name__, url_prefix="/api/events")


@bp.route("", methods=["GET"])
def list_events():
    account_id = request.args.get("account_id", type=int)
    identity_id = request.args.get("identity_id", type=int)
    platform = request.args.get("platform")
    limit = min(request.args.get("limit", 100, type=int), 500)
    offset = request.args.get("offset", 0, type=int)
    events = db.get_events(account_id=account_id, identity_id=identity_id,
                           platform=platform, limit=limit, offset=offset)
    total = db.get_event_count(account_id=account_id, identity_id=identity_id, platform=platform)
    return jsonify({"success": True, "events": events, "total": total})


@bp.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = db.get_event(event_id)
    if not event:
        return jsonify({"success": False, "error": "Not found"}), 404
    if event.get("event_data"):
        try:
            event["event_data_parsed"] = json.loads(event["event_data"])
        except (json.JSONDecodeError, TypeError):
            event["event_data_parsed"] = None
    return jsonify({"success": True, "event": event})
