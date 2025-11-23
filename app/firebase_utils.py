import requests
from flask import request, jsonify
from functools import wraps
from .extensions import db
from .models.core_models import User  # assumes your User model lives here

# --- Firebase Web API Key (from Firebase console → Project Settings → General) ---
FIREBASE_API_KEY = "AIzaSyDkwiWcsUMdylKQnBX95nJO5ukzI9QvEKk"

# --- Allowed email domains ---
ALLOWED_DOMAINS = ["oldfamily.co.uk"]


def verify_firebase_token(token):
    """
    Verifies a Firebase ID token using the REST API.
    Returns a simplified dict with uid, email, and display name.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"idToken": token})

    if res.status_code == 200:
        users = res.json().get("users", [])
        if not users:
            return None

        user_data = users[0]
        email = user_data.get("email")
        return {
            "uid": user_data.get("localId"),
            "email": email,
            "name": user_data.get("displayName") or email.split("@")[0],
        }

    print("❌ Firebase token verification failed:", res.text)
    return None


def firebase_required(f):
    """
    Flask decorator for Firebase authentication.
    1️⃣ Checks the Bearer token.
    2️⃣ Verifies it via Firebase REST API.
    3️⃣ Enforces allowed domain restriction.
    4️⃣ Only then syncs the user with the local DB.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # --- Check for auth header ---
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        # --- Verify Firebase token ---
        token = auth_header.split("Bearer ")[1]
        user = verify_firebase_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired Firebase token"}), 401

        # --- Enforce domain restriction ---
        email = user.get("email", "")
        domain = email.split("@")[-1].lower()
        if domain not in ALLOWED_DOMAINS:
            print(f"🚫 Access denied for {email} (domain: {domain})")
            return jsonify({"error": f"Access restricted to {', '.join(ALLOWED_DOMAINS)}"}), 403

        # --- Sync user to DB *after* domain passes ---
        db_user = User.query.filter_by(email=email).first()
        if not db_user:
            db_user = User(
                id=user["uid"],  # ✅ use Firebase UID as primary key
                name=user["name"],
                email=email,
                role="user"
            )
            db.session.add(db_user)
            db.session.commit()

        # --- Attach DB user ID to request.user for use in routes ---
        user["db_id"] = db_user.id
        request.user = user

        return f(*args, **kwargs)

    return decorated
