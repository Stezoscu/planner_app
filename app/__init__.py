from datetime import timedelta
from flask import Flask
from .extensions import db, cors, jwt
import os
import warnings



warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- Core config ---
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path,'family_hub.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- JWT config ---
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-only-change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    # init extensions
    db.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)

    # models import ensures tables known before create_all
    from .models.core_models import User, Task, Meal, Workout  # noqa

    with app.app_context():
        db.create_all()

    # register blueprints
    from .routes.health import health_bp
    from .routes.users import users_bp
    from .routes.tasks import tasks_bp
    from .routes.meals import meals_bp
    from .routes.workouts import workouts_bp
    from .routes.auth import auth_bp  # <-- NEW
    from .routes.summary import summary_bp
    from .routes.sheets import sheets_bp



    app.register_blueprint(health_bp,   url_prefix="/api/health")
    app.register_blueprint(auth_bp,     url_prefix="/api/auth")   # <-- NEW
    app.register_blueprint(users_bp,    url_prefix="/api/users")
    app.register_blueprint(tasks_bp,    url_prefix="/api/tasks")
    app.register_blueprint(meals_bp,    url_prefix="/api/meals")
    app.register_blueprint(workouts_bp, url_prefix="/api/workouts")
    app.register_blueprint(summary_bp, url_prefix="/api/summary")
    app.register_blueprint(sheets_bp)

    @app.route("/")
    def home():
        return {"message": "Welcome to the Family Hub API!"}

    return app
