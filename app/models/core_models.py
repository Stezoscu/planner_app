from ..extensions import db
from datetime import datetime, date


# --- User Model ---
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.String(128), primary_key=True)  # ✅ Firebase UID (not auto)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default="user")

    tasks = db.relationship("Task", backref="user", lazy=True)
    meals = db.relationship("Meal", backref="user", lazy=True)
    workouts = db.relationship("Workout", backref="user", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}

    def __repr__(self):
        return f"<User {self.email}>"


# --- Task Model ---
class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)

    # --- New recurrence fields ---
    repeat_freq = db.Column(db.String(20), nullable=True)       # daily|weekly|monthly|yearly
    repeat_interval = db.Column(db.Integer, default=1)          # every N [freq]
    repeat_byweekday = db.Column(db.String(50), nullable=True)  # e.g. "MO,WE,FR"
    repeat_until = db.Column(db.Date, nullable=True)
    repeat_count = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        """Serialize task with recurrence info."""
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed": self.completed,
            "user_id": self.user_id,
            "repeat": {
                "freq": self.repeat_freq,
                "interval": self.repeat_interval,
                "byweekday": self.repeat_byweekday.split(",") if self.repeat_byweekday else [],
                "until": self.repeat_until.isoformat() if self.repeat_until else None,
                "count": self.repeat_count,
            } if self.repeat_freq else None,
        }

    def __repr__(self):
        return f"<Task {self.title}>"

# --- Meal Model ---
class Meal(db.Model):
    __tablename__ = "meal"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Integer, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fibre = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date, default=date.today)

    def __repr__(self):
        return f"<Meal {self.name}>"


# --- Workout Model ---
class Workout(db.Model):
    __tablename__ = "workout"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), db.ForeignKey("user.id"), nullable=False)
    activity = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    date = db.Column(db.Date, default=date.today)

    def __repr__(self):
        return f"<Workout {self.activity}>"


class TaskCompletion(db.Model):
    __tablename__ = "task_completion"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    user_id = db.Column(db.String(128), db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=True)

    __table_args__ = (db.UniqueConstraint("task_id", "user_id", "date", name="uq_task_completion"),)
