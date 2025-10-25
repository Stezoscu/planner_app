from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.core_models import Workout
from .auth import is_admin

workouts_bp = Blueprint("workouts", __name__)

# --- Get all workouts (admin can see all; users see their own) ---
@workouts_bp.route("/", methods=["GET"])
@jwt_required()
def get_workouts():
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)
    date_filter = request.args.get("date")
    filter_user_id = request.args.get("user_id", type=int)

    query = Workout.query

    if admin:
        # Admin can view all or filter by user_id
        if filter_user_id:
            query = query.filter_by(user_id=filter_user_id)
    else:
        # Regular user: only their own workouts
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
    ])


# --- Get a single workout ---
@workouts_bp.route("/<int:workout_id>", methods=["GET"])
@jwt_required()
def get_workout(workout_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

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
@jwt_required()
def add_workout():
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)
    data = request.get_json() or {}

    activity = data.get("activity")
    duration = data.get("duration")
    if not activity or not duration:
        return jsonify({"error": "Both 'activity' and 'duration' are required"}), 400

    try:
        workout_date = datetime.fromisoformat(data["date"]).date() if data.get("date") else datetime.now().date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Admins can assign workouts to other users
    assigned_user_id = data.get("user_id", user_id if not admin else None)
    if admin and "user_id" in data:
        assigned_user_id = data["user_id"]
    elif not admin:
        assigned_user_id = user_id

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
@jwt_required()
def update_workout(workout_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

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
@jwt_required()
def delete_workout(workout_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    workout = Workout.query.get_or_404(workout_id)
    if not admin and workout.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    db.session.delete(workout)
    db.session.commit()
    return jsonify({"message": "Workout deleted successfully"})
