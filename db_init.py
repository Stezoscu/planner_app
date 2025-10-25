from app import create_app
from app.extensions import db
from app.models.core_models import User, Task, Meal, Workout
from datetime import datetime, timedelta
import os

app = create_app()

print("\n🔧 Starting database initialisation...\n")
with app.app_context():
    # Clear tables
    print("🧹 Clearing existing data...")
    for model in (Task, Meal, Workout, User):
        db.session.query(model).delete()
    db.session.commit()

    # Create sample users with passwords
    print("👤 Adding users...")
    steve  = User(name="Steve",  email="steve@example.com",  role="admin"); steve.set_password("Passw0rd!")
    alex   = User(name="Alex",   email="alex@example.com",   role="user");  alex.set_password("Passw0rd!")
    jordan = User(name="Jordan", email="jordan@example.com", role="user");  jordan.set_password("Passw0rd!")
    db.session.add_all([steve, alex, jordan])
    db.session.commit()

    # Sample tasks
    print("🗓️ Adding tasks...")
    tasks = [
        Task(
            user_id=steve.id,
            title="Plan weekly meals",
            due_date=datetime.now() + timedelta(days=3),
            completed=False
        ),
        Task(
            user_id=alex.id,
            title="Book gym session",
            due_date=datetime.now() + timedelta(days=1),
            completed=True
        )
    ]
    db.session.add_all(tasks)
    db.session.commit()

    # Sample meals
    print("🍽️ Adding meals...")
    meals = [
        Meal(
            user_id=steve.id,
            name="Chicken stir-fry",
            calories=520,
            date=datetime.now().date()
        ),
        Meal(
            user_id=alex.id,
            name="Pasta with vegetables",
            calories=600,
            date=datetime.now().date() + timedelta(days=1)
        )
    ]
    db.session.add_all(meals)
    db.session.commit()

    # Sample workouts
    print("🏋️ Adding workouts...")
    workouts = [
        Workout(
            user_id=steve.id,
            activity="Cycling",
            duration=45,
            date=datetime.now().date()
        ),
        Workout(
            user_id=alex.id,
            activity="Yoga",
            duration=30,
            date=datetime.now().date() + timedelta(days=2)
        )
    ]
    db.session.add_all(workouts)
    db.session.commit()

    print("\n✅ Database initialisation complete!\n")
    print("📊 Summary:")
    print(f"  Users: {User.query.count()}")
    print(f"  Tasks: {Task.query.count()}")
    print(f"  Meals: {Meal.query.count()}")
    print(f"  Workouts: {Workout.query.count()}\n")
