from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.sheet_mapping import SheetMapping
from ..models.core_models import User
from ..firebase_utils import firebase_required

sheet_mapping_bp = Blueprint("sheet_mapping", __name__)

def is_admin(user):
    """Check admin role from DB."""
    db_user = User.query.filter_by(id=user.get("uid")).first()
    return db_user and db_user.role == "admin"

# --- List all mappings (Admin only) ---
@sheet_mapping_bp.route("/", methods=["GET"])
@firebase_required
def list_mappings():
    user = request.user
    if not is_admin(user):
        return jsonify({"error": "Admin access required"}), 403

    mappings = SheetMapping.query.all()
    return jsonify([
        {"user_id": m.user_id, "sheet_name": m.sheet_name}
        for m in mappings
    ]), 200

# --- Create or update mapping (Admin only) ---
@sheet_mapping_bp.route("/", methods=["POST"])
@firebase_required
def create_mapping():
    user = request.user
    if not is_admin(user):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    user_id = data.get("user_id")
    sheet_name = data.get("sheet_name")

    if not user_id or not sheet_name:
        return jsonify({"error": "Missing 'user_id' or 'sheet_name'"}), 400

    mapping = SheetMapping.query.filter_by(user_id=user_id).first()
    if mapping:
        mapping.sheet_name = sheet_name
    else:
        mapping = SheetMapping(user_id=user_id, sheet_name=sheet_name)
        db.session.add(mapping)

    db.session.commit()
    return jsonify({"message": "Mapping saved successfully"}), 200
