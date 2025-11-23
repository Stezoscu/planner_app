from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.core_models import User
from ..firebase_utils import firebase_required

auth_bp = Blueprint("auth", __name__)


# --- Check or create a Firebase user record in local DB ---
def ensure_user_exists(firebase_user):
    uid = firebase_user.get("uid")
    email = firebase_user.get("email")
    name = firebase_user.get("name") or firebase_user.get("display_name") or "Unknown User"

    if not uid or not email:
        return None

    user = User.query.get(uid)
    if not user:
        user = User(id=uid, email=email, name=name)
        db.session.add(user)
        db.session.commit()
        print(f"🆕 Created new local user record for {email}")
    return user


# --- Get current user info (via Firebase token) ---
@auth_bp.route("/me", methods=["GET"])
@firebase_required
def me():
    firebase_user = getattr(request, "user", None)
    if not firebase_user:
        return jsonify({"error": "Authentication failed"}), 401

    user = ensure_user_exists(firebase_user)
    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        },
        "firebase": firebase_user
    })


# --- (Optional) Admin helper ---
def is_admin(firebase_user):
    """Return True if Firebase user has an admin role in DB."""
    uid = firebase_user.get("uid")
    user = User.query.get(uid)
    return user and user.role == "admin"
