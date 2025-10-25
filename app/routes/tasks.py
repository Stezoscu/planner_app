from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.core_models import Task
from .auth import is_admin

tasks_bp = Blueprint("tasks", __name__)

# --- Get all tasks ---
@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def get_tasks():
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    # Admins can see all tasks or filter by user_id param
    if admin:
        filter_user_id = request.args.get("user_id", type=int)
        query = Task.query
        if filter_user_id:
            query = query.filter_by(user_id=filter_user_id)
        tasks = query.order_by(Task.due_date.is_(None), Task.due_date.asc()).all()
    else:
        # Regular users only see their own
        tasks = (
            Task.query.filter_by(user_id=user_id)
            .order_by(Task.due_date.is_(None), Task.due_date.asc())
            .all()
        )

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "completed": t.completed,
            "user_id": t.user_id
        }
        for t in tasks
    ])


# --- Get a single task ---
@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    task = Task.query.get_or_404(task_id)

    if not admin and task.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    return jsonify({
        "id": task.id,
        "title": task.title,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "completed": task.completed,
        "user_id": task.user_id
    })


# --- Create a new task ---
@tasks_bp.route("/", methods=["POST"])
@jwt_required()
def add_task():
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    data = request.get_json() or {}
    title = data.get("title")
    if not title:
        return jsonify({"error": "Title is required"}), 400

    try:
        due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO 8601 (YYYY-MM-DD)"}), 400

    # Admin can create tasks for other users if user_id provided
    assigned_user_id = data.get("user_id", user_id if not admin else None)
    if admin and "user_id" in data:
        assigned_user_id = data["user_id"]
    elif not admin:
        assigned_user_id = user_id

    new_task = Task(
        title=title,
        due_date=due_date,
        completed=data.get("completed", False),
        user_id=assigned_user_id,
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        "message": "Task added successfully",
        "id": new_task.id
    }), 201


# --- Update a task ---
@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    task = Task.query.get_or_404(task_id)
    if not admin and task.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    data = request.get_json() or {}

    task.title = data.get("title", task.title)
    if "due_date" in data:
        try:
            task.due_date = datetime.fromisoformat(data["due_date"]) if data["due_date"] else None
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    task.completed = data.get("completed", task.completed)

    db.session.commit()
    return jsonify({"message": "Task updated successfully"})


# --- Delete a task ---
@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    task = Task.query.get_or_404(task_id)
    if not admin and task.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted successfully"})
