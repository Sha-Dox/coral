from flask import Blueprint, request, jsonify
import database as db

bp = Blueprint("identities", __name__, url_prefix="/api/identities")


@bp.route("", methods=["GET"])
def list_identities():
    identities = db.get_all_identities()
    for ident in identities:
        ident["latest_event"] = db.get_identity_latest_event(ident["id"])
    return jsonify({"success": True, "identities": identities})


@bp.route("", methods=["POST"])
def create_identity():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "Name is required"}), 400
    identity_id = db.add_identity(name, data.get("notes"))
    return jsonify({"success": True, "id": identity_id}), 201


@bp.route("/<int:identity_id>", methods=["GET"])
def get_identity(identity_id):
    ident = db.get_identity(identity_id)
    if not ident:
        return jsonify({"success": False, "error": "Not found"}), 404
    ident["latest_event"] = db.get_identity_latest_event(identity_id)
    return jsonify({"success": True, "identity": ident})


@bp.route("/<int:identity_id>", methods=["PUT"])
def update_identity(identity_id):
    data = request.get_json() or {}
    ok = db.update_identity(identity_id, **{k: data[k] for k in ("name", "notes") if k in data})
    if not ok:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True})


@bp.route("/<int:identity_id>", methods=["DELETE"])
def delete_identity(identity_id):
    if not db.delete_identity(identity_id):
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True})


@bp.route("/<int:identity_id>/accounts", methods=["POST"])
def add_account(identity_id):
    data = request.get_json() or {}
    platform = (data.get("platform") or "").strip().lower()
    username = (data.get("username") or "").strip()
    if not platform or not username:
        return jsonify({"success": False, "error": "platform and username are required"}), 400
    if platform not in ("instagram", "pinterest", "spotify"):
        return jsonify({"success": False, "error": f"Unknown platform: {platform}"}), 400

    config_json = None
    if data.get("config"):
        import json
        config_json = json.dumps(data["config"])

    account_id = db.add_account(identity_id, platform, username,
                                 display_name=data.get("display_name"), config_json=config_json)
    if not account_id:
        return jsonify({"success": False, "error": "Account already exists on this platform"}), 409
    return jsonify({"success": True, "id": account_id}), 201
