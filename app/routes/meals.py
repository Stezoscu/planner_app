from flask import Blueprint, jsonify, request
from datetime import datetime
from ..extensions import db
from ..models.core_models import Meal
from ..firebase_utils import firebase_required

meals_bp = Blueprint("meals", __name__)

# --- Get all meals ---
@meals_bp.route("/", methods=["GET"])
@firebase_required
def get_meals():
    user = request.user
    user_id = user.get("uid")

    date_filter = request.args.get("date")

    query = Meal.query.filter_by(user_id=user_id)

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
        }
        for m in meals
    ]), 200


# --- Get a single meal ---
@meals_bp.route("/<int:meal_id>", methods=["GET"])
@firebase_required
def get_meal(meal_id):
    user = request.user
    user_id = user.get("uid")

    meal = Meal.query.get_or_404(meal_id)
    if meal.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    return jsonify({
        "id": meal.id,
        "name": meal.name,
        "calories": meal.calories,
        "protein": meal.protein,
        "carbs": meal.carbs,
        "fibre": meal.fibre,
        "date": meal.date.isoformat(),
    }), 200


# --- Create a new meal ---
@meals_bp.route("/", methods=["POST"])
@firebase_required
def add_meal():
    user = request.user
    user_id = user.get("uid")
    data = request.get_json() or {}

    name = data.get("name")
    if not name:
        return jsonify({"error": "Meal name is required"}), 400

    try:
        meal_date = datetime.fromisoformat(data["date"]).date() if data.get("date") else datetime.now().date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    new_meal = Meal(
        name=name,
        calories=data.get("calories"),
        protein=data.get("protein"),
        carbs=data.get("carbs"),
        fibre=data.get("fibre"),
        date=meal_date,
        user_id=user_id,
    )

    db.session.add(new_meal)
    db.session.commit()
    return jsonify({"message": "Meal added successfully", "id": new_meal.id}), 201


# --- Update a meal ---
@meals_bp.route("/<int:meal_id>", methods=["PUT"])
@firebase_required
def update_meal(meal_id):
    user = request.user
    user_id = user.get("uid")

    meal = Meal.query.get_or_404(meal_id)
    if meal.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    data = request.get_json() or {}

    for field in ["name", "calories", "protein", "carbs", "fibre"]:
        if field in data:
            setattr(meal, field, data[field])

    if data.get("date"):
        try:
            meal.date = datetime.fromisoformat(data["date"]).date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    db.session.commit()
    return jsonify({"message": "Meal updated successfully"}), 200


# --- Delete a meal ---
@meals_bp.route("/<int:meal_id>", methods=["DELETE"])
@firebase_required
def delete_meal(meal_id):
    user = request.user
    user_id = user.get("uid")

    meal = Meal.query.get_or_404(meal_id)
    if meal.user_id != user_id:
        return jsonify({"error": "Not authorised"}), 403

    db.session.delete(meal)
    db.session.commit()
    return jsonify({"message": "Meal deleted successfully"}), 200
