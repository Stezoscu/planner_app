from ..extensions import db
from datetime import datetime, timedelta, date
from passlib.hash import bcrypt
from hashlib import sha256


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), default="user")

    tasks = db.relationship("Task", backref="user", lazy=True)
    meals = db.relationship("Meal", backref="user", lazy=True)
    workouts = db.relationship("Workout", backref="user", lazy=True)

    def set_password(self, raw_password: str):
        """Hash a password safely using SHA256 pre-hash + bcrypt."""
        if not raw_password:
            raise ValueError("Password cannot be empty.")
        # First hash with SHA-256, then bcrypt that digest
        digest = sha256(raw_password.encode("utf-8")).hexdigest()
        self.password_hash = bcrypt.hash(digest)

    def check_password(self, raw_password: str) -> bool:
        """Verify password by comparing SHA256 digest before bcrypt verification."""
        if not self.password_hash or not raw_password:
            return False
        digest = sha256(raw_password.encode("utf-8")).hexdigest()
        return bcrypt.verify(digest, self.password_hash)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}

    def __repr__(self):
        return f"<User {self.email}>"



class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Task {self.title}>"


class Meal(db.Model):
    __tablename__ = "meal"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Integer, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fibre = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date, default=date.today)

    def __repr__(self):
        return f"<Meal {self.name}>"


class Workout(db.Model):
    __tablename__ = "workout"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    date = db.Column(db.Date, default=date.today)

    def __repr__(self):
        return f"<Workout {self.activity}>"
