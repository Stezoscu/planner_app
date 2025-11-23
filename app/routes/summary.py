from flask import Blueprint, jsonify, request
from datetime import datetime, date
from ..extensions import db
from ..models.core_models import Task, Meal, Workout, User
from ..firebase_utils import firebase_required

summary_bp = Blueprint("summary", __name__)

# --- Helper: Check admin role ---
def is_admin(user):
    """Check if the Firebase-authenticated user is an admin in the DB."""
    db_user = User.query.filter_by(id=user.get("uid")).first()
    return db_user and db_user.role == "admin"


# --- Today's summary ---
@summary_bp.route("/today", methods=["GET"])
@firebase_required
def get_today_summary():
    """
    Return today's tasks, meals, and workouts for the current user,
    or another user's if admin passes ?user_id=.
    """
    user = request.user
    user_id = user.get("uid")
    admin = is_admin(user)
    query_user_id = request.args.get("user_id")

    if query_user_id:
        if admin:
            user_id = query_user_id
        else:
            return jsonify({"error": "Admin access required to view other users’ summaries"}), 403

    today = date.today()

    tasks = (
        Task.query.filter_by(user_id=user_id)
        .filter(db.func.date(Task.due_date) == today)
        .all()
    )
    meals = (
        Meal.query.filter_by(user_id=user_id)
        .filter(db.func.date(Meal.date) == today)
        .all()
    )
    workouts = (
        Workout.query.filter_by(user_id=user_id)
        .filter(db.func.date(Workout.date) == today)
        .all()
    )

    summary = {
        "date": today.isoformat(),
        "tasks": [
            {"id": t.id, "title": t.title, "due_date": t.due_date, "completed": t.completed}
            for t in tasks
        ],
        "meals": [
            {
                "id": m.id,
                "name": m.name,
                "calories": m.calories,
                "protein": m.protein,
                "carbs": m.carbs,
                "fibre": m.fibre,
            }
            for m in meals
        ],
        "workouts": [
            {"id": w.id, "activity": w.activity, "duration": w.duration}
            for w in workouts
        ],
    }

    return jsonify(summary), 200


# --- Range summary ---
@summary_bp.route("/range", methods=["GET"])
@firebase_required
def get_range_summary():
    """
    Return tasks, meals, and workouts for a date range (inclusive).
    Query params: ?start=YYYY-MM-DD&end=YYYY-MM-DD[&user_id=]
    """
    user = request.user
    user_id = user.get("uid")
    admin = is_admin(user)
    query_user_id = request.args.get("user_id")

    if query_user_id:
        if admin:
            user_id = query_user_id
        else:
            return jsonify({"error": "Admin access required to view other users’ data"}), 403

    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if not start_str or not end_str:
        return jsonify({"error": "Both 'start' and 'end' query parameters are required"}), 400

    try:
        start_date = datetime.fromisoformat(start_str).date()
        end_date = datetime.fromisoformat(end_str).date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    if end_date < start_date:
        return jsonify({"error": "End date cannot be before start date"}), 400

    return _get_summary_for_range(user_id, start_date, end_date)


# --- Helper shared by both endpoints ---
def _get_summary_for_range(user_id, start_date, end_date):
    tasks = (
        Task.query.filter_by(user_id=user_id)
        .filter(db.func.date(Task.due_date).between(start_date, end_date))
        .all()
    )
    meals = (
        Meal.query.filter_by(user_id=user_id)
        .filter(db.func.date(Meal.date).between(start_date, end_date))
        .all()
    )
    workouts = (
        Workout.query.filter_by(user_id=user_id)
        .filter(db.func.date(Workout.date).between(start_date, end_date))
        .all()
    )

    total_calories = sum(m.calories or 0 for m in meals)
    total_protein = sum(m.protein or 0 for m in meals)
    total_carbs = sum(m.carbs or 0 for m in meals)
    total_fibre = sum(m.fibre or 0 for m in meals)
    total_workout_duration = sum(w.duration or 0 for w in workouts)
    completed_task_count = sum(1 for t in tasks if t.completed)
    total_task_count = len(tasks)

    summary = {
        "range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "totals": {
            "total_calories": total_calories,
            "total_protein": total_protein,
            "total_carbs": total_carbs,
            "total_fibre": total_fibre,
            "total_workout_duration": total_workout_duration,
            "completed_task_count": completed_task_count,
            "total_task_count": total_task_count,
        },
        "tasks": [
            {"id": t.id, "title": t.title, "due_date": t.due_date, "completed": t.completed}
            for t in tasks
        ],
        "meals": [
            {
                "id": m.id,
                "name": m.name,
                "calories": m.calories,
                "protein": m.protein,
                "carbs": m.carbs,
                "fibre": m.fibre,
            }
            for m in meals
        ],
        "workouts": [
            {
                "id": w.id,
                "activity": w.activity,
                "duration": w.duration,
                "date": w.date.isoformat(),
            }
            for w in workouts
        ],
    }

    return jsonify(summary), 200
