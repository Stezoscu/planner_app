from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.core_models import User
from .auth import is_admin

users_bp = Blueprint("users", __name__)

# --- List all users (Admin only) ---
@users_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    identity = get_jwt_identity()
    if not is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403

    users = User.query.all()
    return jsonify([
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
        for u in users
    ])


# --- Create a user (Admin only) ---
@users_bp.route("/", methods=["POST"])
@jwt_required()
def create_user():
    identity = get_jwt_identity()
    if not is_admin(identity):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(force=True, silent=False)
    if not all(k in data for k in ["name", "email"]):
        return jsonify({"error": "Missing name or email"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already in use"}), 409

    new_user = User(
        name=data["name"],
        email=data["email"].strip().lower(),
        role=data.get("role", "user")
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "id": new_user.id}), 201
