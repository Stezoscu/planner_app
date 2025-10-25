from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.core_models import Meal
from .auth import is_admin

meals_bp = Blueprint("meals", __name__)

# --- Get all meals (admin can see all; users see their own) ---
@meals_bp.route("/", methods=["GET"])
@jwt_required()
def get_meals():
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)
    date_filter = request.args.get("date")
    filter_user_id = request.args.get("user_id", type=int)

    query = Meal.query

    if admin:
        # Admin can filter by user_id
        if filter_user_id:
            query = query.filter_by(user_id=filter_user_id)
    else:
        # Regular users only see their own
        query = query.filter_by(user_id=user_id)

    # Optional date filter
    if date_filter:
        try:
            parsed_date = datetime.fromisoformat(date_filter).date()
            query = query.filter(Meal.date == parsed_date)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    meals = query.order_by(Meal.date.desc()).all()

    return jsonify([
        {
            "id": m.id,
            "name": m.name,
            "calories": m.calories,
            "protein": m.protein,
            "carbs": m.carbs,
            "fibre": m.fibre,
            "date": m.date.isoformat(),
            "user_id": m.user_id
        }
        for m in meals
    ])


# --- Get a single meal ---
@meals_bp.route("/<int:meal_id>", methods=["GET"])
@jwt_required()
def get_meal(meal_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    meal = Meal.query.get_or_404(meal_id)
    if not admin and meal.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    return jsonify({
        "id": meal.id,
        "name": meal.name,
        "calories": meal.calories,
        "protein": meal.protein,
        "carbs": meal.carbs,
        "fibre": meal.fibre,
        "date": meal.date.isoformat(),
        "user_id": meal.user_id
    })


# --- Create a new meal ---
@meals_bp.route("/", methods=["POST"])
@jwt_required()
def add_meal():
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)
    data = request.get_json() or {}

    name = data.get("name")
    if not name:
        return jsonify({"error": "Meal name is required"}), 400

    try:
        meal_date = datetime.fromisoformat(data["date"]).date() if data.get("date") else datetime.now().date()
    except ValueError:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    # Admin can assign meals to other users
    assigned_user_id = data.get("user_id", user_id if not admin else None)
    if admin and "user_id" in data:
        assigned_user_id = data["user_id"]
    elif not admin:
        assigned_user_id = user_id

    new_meal = Meal(
        name=name,
        calories=data.get("calories"),
        protein=data.get("protein"),
        carbs=data.get("carbs"),
        fibre=data.get("fibre"),
        date=meal_date,
        user_id=assigned_user_id
    )

    db.session.add(new_meal)
    db.session.commit()
    return jsonify({"message": "Meal added successfully", "id": new_meal.id}), 201


# --- Update a meal ---
@meals_bp.route("/<int:meal_id>", methods=["PUT"])
@jwt_required()
def update_meal(meal_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    meal = Meal.query.get_or_404(meal_id)
    if not admin and meal.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    data = request.get_json() or {}

    for field in ["name", "calories", "protein", "carbs", "fibre"]:
        if field in data:
            setattr(meal, field, data[field])

    if data.get("date"):
        try:
            meal.date = datetime.fromisoformat(data["date"]).date()
        except ValueError:
            return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    db.session.commit()
    return jsonify({"message": "Meal updated successfully"})


# --- Delete a meal ---
@meals_bp.route("/<int:meal_id>", methods=["DELETE"])
@jwt_required()
def delete_meal(meal_id):
    identity = get_jwt_identity()
    user_id = int(identity) if isinstance(identity, str) else identity.get("id")
    admin = is_admin(identity)

    meal = Meal.query.get_or_404(meal_id)
    if not admin and meal.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    db.session.delete(meal)
    db.session.commit()
    return jsonify({"message": "Meal deleted successfully"})
