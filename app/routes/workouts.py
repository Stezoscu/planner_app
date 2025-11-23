from flask import Blueprint, jsonify, request
from datetime import datetime
from ..extensions import db
from ..models.core_models import Workout, User
from ..firebase_utils import firebase_required

workouts_bp = Blueprint("workouts", __name__)

# --- Helper: Check admin role ---
def is_admin(user):
    """Check if the Firebase-authenticated user is an admin in the DB."""
    db_user = User.query.filter_by(id=user.get("uid")).first()
    return db_user and db_user.role == "admin"


# --- Get all workouts (admin can see all; users see their own) ---
@workouts_bp.route("/", methods=["GET"])
@firebase_required
def get_workouts():
    user = request.user
    user_id = user.get("uid")
    admin = is_admin(user)
    date_filter = request.args.get("date")
    filter_user_id = request.args.get("user_id")

    query = Workout.query

    if admin and filter_user_id:
        query = query.filter_by(user_id=filter_user_id)
    elif not admin:
        query = query.filter_by(user_id=user_id)

    # Optional date filter
    if date_filter:
        try:
            parsed_date = datetime.fromisoformat(date_filter).date()
            query = query.filter(Workout.date == parsed_date)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    workouts = query.order_by(Workout.date.desc()).all()

    return jsonify([
        {
            "id": w.id,
            "activity": w.activity,
            "duration": w.duration,
            "date": w.date.isoformat(),
            "user_id": w.user_id
        }
        for w in workouts
    ]), 200


# --- Get a single workout ---
@workouts_bp.route("/<int:workout_id>", methods=["GET"])
@firebase_required
def get_workout(workout_id):
    user = request.user
    user_id = user.get("uid")
    admin = is_admin(user)

    workout = Workout.query.get_or_404(workout_id)
    if not admin and workout.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    return jsonify({
        "id": workout.id,
        "activity": workout.activity,
        "duration": workout.duration,
        "date": workout.date.isoformat(),
        "user_id": workout.user_id
    })


# --- Create a new workout ---
@workouts_bp.route("/", methods=["POST"])
@firebase_required
def add_workout():
    user = request.user
    user_id = user.get("uid")
    admin = is_admin(user)
    data = request.get_json() or {}

    activity = data.get("activity")
    duration = data.get("duration")
    if not activity or not duration:
        return jsonify({"error": "Both 'activity' and 'duration' are required"}), 400

    try:
        workout_date = datetime.fromisoformat(data.get("date")).date() if data.get("date") else datetime.now().date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    assigned_user_id = data.get("user_id") if admin and "user_id" in data else user_id

    new_workout = Workout(
        activity=activity,
        duration=duration,
        date=workout_date,
        user_id=assigned_user_id
    )

    db.session.add(new_workout)
    db.session.commit()
    return jsonify({"message": "Workout added successfully", "id": new_workout.id}), 201


# --- Update a workout ---
@workouts_bp.route("/<int:workout_id>", methods=["PUT"])
@firebase_required
def update_workout(workout_id):
    user = request.user
    user_id = user.get("uid")
    admin = is_admin(user)

    workout = Workout.query.get_or_404(workout_id)
    if not admin and workout.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    data = request.get_json() or {}

    if "activity" in data:
        workout.activity = data["activity"]
    if "duration" in data:
        workout.duration = data["duration"]
    if "date" in data:
        try:
            workout.date = datetime.fromisoformat(data["date"]).date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    db.session.commit()
    return jsonify({"message": "Workout updated successfully"})


# --- Delete a workout ---
@workouts_bp.route("/<int:workout_id>", methods=["DELETE"])
@firebase_required
def delete_workout(workout_id):
    user = request.user
    user_id = user.get("uid")
    admin = is_admin(user)

    workout = Workout.query.get_or_404(workout_id)
    if not admin and workout.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    db.session.delete(workout)
    db.session.commit()
    return jsonify({"message": "Workout deleted successfully"})
