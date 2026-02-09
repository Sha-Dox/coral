from flask import Blueprint, request, jsonify
import database as db

bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")


@bp.route("/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    data = request.get_json() or {}
    fields = {}
    for key in ("enabled", "display_name", "config_json"):
        if key in data:
            fields[key] = data[key]
    if not fields:
        return jsonify({"success": False, "error": "Nothing to update"}), 400
    if not db.update_account(account_id, **fields):
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True})


@bp.route("/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    if not db.delete_account(account_id):
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True})


@bp.route("/<int:account_id>/boards", methods=["GET"])
def get_boards(account_id):
    boards = db.get_pinterest_boards(account_id)
    return jsonify({"success": True, "boards": boards})
