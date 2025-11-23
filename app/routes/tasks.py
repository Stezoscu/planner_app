from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from ..extensions import db
from ..models.core_models import Task, TaskCompletion  # ✅ NEW
from ..firebase_utils import firebase_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


# --- Small util to expand recurring tasks into the requested window ---
def expand_task_occurrences(task, from_date, to_date):
    """Generate task occurrences within [from_date, to_date]."""
    if not task.repeat_freq or not task.due_date:
        return [task]

    occurrences = []
    base = task.due_date.date()
    freq = task.repeat_freq
    interval = task.repeat_interval or 1
    until = task.repeat_until
    count = task.repeat_count
    weekdays = (
        [w.strip().upper() for w in task.repeat_byweekday.split(",")]
        if task.repeat_byweekday else []
    )

    current = base
    i = 0
    max_occurrences = 1000  # 🔒 safety limit

    while True:
        if current >= from_date and current <= to_date:
            # Match weekday if applicable
            if not weekdays or current.strftime("%a")[:2].upper() in weekdays:
                clone = Task(
                    id=task.id,
                    title=task.title,
                    due_date=datetime.combine(current, task.due_date.time()),
                    completed=task.completed,
                    user_id=task.user_id,
                )
                occurrences.append(clone)

        # --- stop conditions ---
        if until and current > until:
            break
        if count and i >= count:
            break
        if (not until and not count and current > to_date):
            break  # ⛔ stop at end of request window
        if i > max_occurrences:
            print(f"⚠️ Too many occurrences for task {task.id}, stopping early")
            break

        # --- increment date ---
        if freq == "daily":
            current += timedelta(days=interval)
        elif freq == "weekly":
            current += timedelta(weeks=interval)
        elif freq == "monthly":
            # naive month add
            month = (current.month - 1 + interval) % 12 + 1
            year = current.year + (current.month - 1 + interval) // 12
            day = min(current.day, 28)
            current = current.replace(year=year, month=month, day=day)
        elif freq == "yearly":
            current = current.replace(year=current.year + interval)
        else:
            break

        i += 1

    return occurrences


# --- GET /api/tasks --------------------------------------------------------
@tasks_bp.route("", methods=["GET"])
@firebase_required
def get_tasks():
    print("⚙️  /api/tasks called with args:", request.args)
    user = request.user
    user_id = user["uid"]

    from_str = request.args.get("from")
    to_str = request.args.get("to")

    try:
        from_date = datetime.strptime(from_str, "%Y-%m-%d").date() if from_str else datetime.utcnow().date()
        to_date = datetime.strptime(to_str, "%Y-%m-%d").date() if to_str else from_date + timedelta(days=7)
    except Exception as e:
        return jsonify({"error": f"Invalid date format: {str(e)}"}), 400

    base_tasks = Task.query.filter_by(user_id=user_id).all()
    expanded = []
    for t in base_tasks:
        expanded += expand_task_occurrences(t, from_date, to_date)

    # ✅ Get per-day completions
    completions = TaskCompletion.query.filter(
        TaskCompletion.user_id == user_id,
        TaskCompletion.date >= from_date,
        TaskCompletion.date <= to_date
    ).all()
    completed_map = {(c.task_id, c.date): True for c in completions}

    result = []
    for t in expanded:
        td = t.to_dict()
        key = (t.id, t.due_date.date())
        td["completed"] = completed_map.get(key, False)
        result.append(td)

    result.sort(key=lambda t: (t["due_date"] or "9999-12-31"))
    print(f"✅ Returning {len(result)} expanded tasks with completions")

    return jsonify(result)


# --- GET single task -------------------------------------------------------
@tasks_bp.route("/<int:task_id>", methods=["GET"])
@firebase_required
def get_task(task_id):
    user = request.user
    task = Task.query.get_or_404(task_id)
    if str(task.user_id) != str(user["uid"]):
        return jsonify({"error": "Not authorised"}), 403

    return jsonify({
        "id": task.id,
        "title": task.title,
        "notes": task.notes,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "completed": task.completed,
        "repeat": {
            "freq": task.repeat_freq,
            "interval": task.repeat_interval,
            "byweekday": task.repeat_byweekday.split(",") if task.repeat_byweekday else [],
            "until": task.repeat_until.isoformat() if task.repeat_until else None,
            "count": task.repeat_count,
        } if task.repeat_freq else None
    })


# --- POST create task ------------------------------------------------------
@tasks_bp.route("", methods=["POST"])
@firebase_required
def add_task():
    user = request.user
    data = request.get_json() or {}
    title = data.get("title")
    if not title:
        return jsonify({"error": "Title is required"}), 400

    date_str = data.get("due_date") or data.get("date")
    due_date = None
    if date_str:
        try:
            due_date = datetime.fromisoformat(date_str)
        except Exception:
            return jsonify({"error": f"Invalid date format: {date_str}"}), 400

    repeat = data.get("repeat") or {}
    repeat_freq = data.get("repeat_freq") or repeat.get("freq")
    repeat_interval = data.get("repeat_interval") or repeat.get("interval", 1)
    repeat_until = data.get("repeat_until") or repeat.get("until")
    repeat_count = data.get("repeat_count") or repeat.get("count")
    repeat_byweekday = (
        data.get("repeat_byweekday") or
        ",".join(repeat.get("byweekday", [])) if repeat.get("byweekday") else None
    )

    new_task = Task(
        title=title,
        due_date=due_date,
        completed=data.get("completed", False),
        user_id=user["uid"],
        repeat_freq=repeat_freq,
        repeat_interval=repeat_interval,
        repeat_byweekday=repeat_byweekday,
        repeat_until=datetime.fromisoformat(repeat_until).date() if repeat_until else None,
        repeat_count=repeat_count,
    )

    db.session.add(new_task)
    db.session.commit()
    print(f"🆕 Task created for {user['email']}: {title}")
    return jsonify({"message": "Task added", "id": new_task.id}), 201


# --- PUT / PATCH update task ------------------------------------------------
@tasks_bp.route("/<int:task_id>", methods=["PUT", "PATCH"])
@firebase_required
def update_task(task_id):
    user = request.user
    task = Task.query.get_or_404(task_id)
    if str(task.user_id) != str(user["uid"]):
        return jsonify({"error": "Not authorised"}), 403

    data = request.get_json() or {}

    if "title" in data:
        task.title = data["title"]
    if "notes" in data:
        task.notes = data["notes"]
    if "completed" in data:
        task.completed = bool(data["completed"])

    if "due_date" in data:
        date_str = data.get("due_date")
        task.due_date = datetime.fromisoformat(date_str) if date_str else None

    if "repeat" in data:
        r = data["repeat"]
        if r is None:
            task.repeat_freq = None
            task.repeat_interval = 1
            task.repeat_byweekday = None
            task.repeat_until = None
            task.repeat_count = None
        else:
            task.repeat_freq = r.get("freq")
            task.repeat_interval = r.get("interval", 1)
            task.repeat_byweekday = ",".join(r.get("byweekday", [])) if r.get("byweekday") else None
            task.repeat_until = datetime.fromisoformat(r["until"]).date() if r.get("until") else None
            task.repeat_count = r.get("count")

    db.session.commit()
    print(f"✏️ Updated task {task.id} ({task.title}) for {user['email']}")
    return jsonify({"message": "Task updated", "id": task.id})


# --- PATCH toggle per-day completion -------------------------------------- ✅ NEW
@tasks_bp.route("/<int:task_id>/toggle", methods=["PATCH"])
@firebase_required
def toggle_task_completion(task_id):
    user = request.user
    data = request.get_json() or {}
    date_str = data.get("date")

    if not date_str:
        return jsonify({"error": "Missing date"}), 400

    try:
        target_date = datetime.fromisoformat(date_str).date()
    except Exception:
        return jsonify({"error": f"Invalid date: {date_str}"}), 400

    task = Task.query.get_or_404(task_id)
    if str(task.user_id) != str(user["uid"]):
        return jsonify({"error": "Not authorised"}), 403

    completion = TaskCompletion.query.filter_by(
        task_id=task_id, user_id=user["uid"], date=target_date
    ).first()

    if completion:
        db.session.delete(completion)
        db.session.commit()
        print(f"🔁 Unmarked task {task_id} for {target_date}")
        return jsonify({"completed": False})
    else:
        new_completion = TaskCompletion(
            task_id=task_id, user_id=user["uid"], date=target_date, completed=True
        )
        db.session.add(new_completion)
        db.session.commit()
        print(f"✅ Marked task {task_id} completed for {target_date}")
        return jsonify({"completed": True})


# --- DELETE task ----------------------------------------------------------
@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@firebase_required
def delete_task(task_id):
    user = request.user
    task = Task.query.get_or_404(task_id)
    if str(task.user_id) != str(user["uid"]):
        return jsonify({"error": "Not authorised"}), 403
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"})
