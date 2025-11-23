from flask import Blueprint, request, jsonify
from firebase_admin import auth
from ..extensions import db
from ..models.core_models import User
from ..firebase_utils import firebase_required

users_bp = Blueprint("users", __name__)

# --- Helper: check if Firebase user is admin ---
def is_admin(user):
    """Check if the current Firebase-authenticated user is an admin."""
    db_user = User.query.filter_by(id=user.get("uid")).first()
    if db_user and db_user.role == "admin":
        return True
    if user.get("admin", False):
        return True
    return False


# --- List all users (Admin only) ---
@users_bp.route("/", methods=["GET"])
@firebase_required
def list_users():
    user = request.user
    if not is_admin(user):
        return jsonify({"error": "Admin access required"}), 403

    users = User.query.all()
    return jsonify([
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
        for u in users
    ]), 200


# --- Create a new user (Admin only) ---
@users_bp.route("/", methods=["POST"])
@firebase_required
def create_user():
    user = request.user
    if not is_admin(user):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(force=True, silent=False)
    if not data or "name" not in data or "email" not in data:
        return jsonify({"error": "Missing name or email"}), 400

    email = data["email"].strip().lower()

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 409

    new_user = User(
        id=data.get("uid"),  # optional pre-registered Firebase UID
        name=data["name"],
        email=email,
        role=data.get("role", "user"),
    )

    db.session.add(new_user)
    db.session.commit()

    # 🔄 Sync role to Firebase (optional)
    try:
        auth.set_custom_user_claims(new_user.id, {"admin": new_user.role == "admin"})
        print(f"✅ Synced role '{new_user.role}' to Firebase for {new_user.email}")
    except Exception as e:
        print(f"⚠️ Firebase role sync failed: {e}")

    return jsonify({"message": "User created successfully", "id": new_user.id}), 201


# --- Update an existing user's role (Admin only) ---
@users_bp.route("/<string:user_id>", methods=["PATCH"])
@firebase_required
def update_user(user_id):
    admin_user = request.user
    if not is_admin(admin_user):
        return jsonify({"error": "Admin access required"}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    # Only name and role can be changed for now
    if "name" in data:
        user.name = data["name"]
    if "role" in data:
        old_role = user.role
        user.role = data["role"]

        # 🔄 Sync Firebase custom claims
        try:
            auth.set_custom_user_claims(user.id, {"admin": user.role == "admin"})
            print(f"🔁 Role changed: {user.email} ({old_role} → {user.role}) synced to Firebase.")
        except Exception as e:
            print(f"⚠️ Failed to sync Firebase custom claim: {e}")

    db.session.commit()

    return jsonify({
        "message": "User updated successfully",
        "id": user.id,
        "role": user.role,
        "name": user.name
    }), 200


# --- Delete a user (Admin only) ---
@users_bp.route("/<string:user_id>", methods=["DELETE"])
@firebase_required
def delete_user(user_id):
    admin_user = request.user
    if not is_admin(admin_user):
        return jsonify({"error": "Admin access required"}), 403

    user = User.query.get_or_404(user_id)

    try:
        # Remove Firebase user
        auth.delete_user(user.id)
        print(f"🗑️ Deleted Firebase user: {user.email}")
    except Exception as e:
        print(f"⚠️ Failed to delete Firebase user: {e}")

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200
