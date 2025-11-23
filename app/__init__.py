from datetime import timedelta
from flask import Flask
import os
import warnings
from dotenv import load_dotenv
from config import Config

# --- Load environment variables ---
load_dotenv()
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")

# --- Initialise extensions ---
from app.extensions import db, cors, jwt, migrate


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.url_map.strict_slashes = False
    os.makedirs(app.instance_path, exist_ok=True)

    # --- Database config ---
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path, 'family_hub.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- JWT config ---
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-only-change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    # --- Initialise extensions ---
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # --- Import models before create_all ---
    from app.models.core_models import User, Task, Meal, Workout  # noqa

    with app.app_context():
        db.create_all()

    # --- Firebase Initialization ---
    try:
        from firebase_admin import credentials, initialize_app

        FIREBASE_KEY_PATH = "/secrets/firebase-key.json"

        if os.path.exists(FIREBASE_KEY_PATH):
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            initialize_app(cred)
            print("✅ Firebase initialized successfully.")
        else:
            print("⚠️ Firebase key not found — skipping initialization.")
    except Exception as e:
        print(f"⚠️ Firebase initialization failed: {e}")

    # --- Register blueprints ---
    from app.routes.health import health_bp
    from app.routes.users import users_bp
    from app.routes.tasks import tasks_bp
    from app.routes.meals import meals_bp
    from app.routes.workouts import workouts_bp
    from app.routes.auth import auth_bp
    from app.routes.summary import summary_bp
    from app.routes.sheets import sheets_bp
    from app.routes.agenda import agenda_bp
    from app.routes.dinner import dinner_bp
    from .routes.sheet_mapping import sheet_mapping_bp
    from .routes.lunches import lunches_bp

    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(meals_bp, url_prefix="/api/meals")
    app.register_blueprint(workouts_bp, url_prefix="/api/workouts")
    app.register_blueprint(summary_bp, url_prefix="/api/summary")
    app.register_blueprint(sheets_bp)
    app.register_blueprint(agenda_bp, url_prefix="/api/agenda")
    app.register_blueprint(dinner_bp, url_prefix="/api/dinner")
    app.register_blueprint(sheet_mapping_bp, url_prefix="/api/sheet_mapping")
    app.register_blueprint(lunches_bp, url_prefix="/api/lunches")

    # --- Root route ---
    @app.route("/")
    def home():
        return {"message": "Welcome to the Family Hub API!"}

    return app
 