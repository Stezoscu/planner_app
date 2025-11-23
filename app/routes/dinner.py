from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from ..firebase_utils import firebase_required
from ..google_auth import get_gsheet_service
import os
import re

dinner_bp = Blueprint("dinner", __name__)

SPREADSHEET_ID = os.getenv("SHEET_ID")
TEMPLATE_SHEET = "Standard Week"


# --- Utility: find target sheet title (handles ?date or ?week) ---
def resolve_week_title(service, target_date):
    ss = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    week_sheets = []
    for s in ss.get("sheets", []):
        title = s["properties"]["title"]
        m = re.search(r"WC\s(\d{1,2})/(\d{1,2})/(\d{2,4})", title)
        if not m:
            continue
        d, mth, y = map(int, m.groups())
        if y < 100:
            y += 2000
        wc_date = datetime(y, mth, d).date()
        week_sheets.append((wc_date, title))

    # Find the sheet where target_date falls within that week
    for wc_date, title in sorted(week_sheets):
        if wc_date <= target_date <= wc_date + timedelta(days=6):
            return title

    return None  # Not found


@dinner_bp.route("/", methods=["GET"])
@firebase_required
def get_dinner():
    """
    Returns the weekly dinner plan from the fixed range (G20:H27) in the Google Sheet.
    Query params:
      ?date=YYYY-MM-DD   → specific day (auto-resolves correct WC sheet)
      ?week=WC dd/mm/yy  → specific sheet
      ?list=1             → list available 'WC dd/mm/yy' sheets
    """
    try:
        if not SPREADSHEET_ID:
            return jsonify({"error": "SHEET_ID not configured"}), 400

        service = get_gsheet_service()

        # === Handle list=1 ===
        if request.args.get("list") == "1":
            ss = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            week_titles = [
                s["properties"]["title"]
                for s in ss.get("sheets", [])
                if s["properties"]["title"].startswith("WC ")
            ]
            week_titles.sort()
            return jsonify({
                "available_weeks": week_titles,
                "count": len(week_titles)
            })

        # === Determine target week ===
        date_param = request.args.get("date")
        week_param = request.args.get("week")

        if week_param:
            target_title = week_param
        elif date_param:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            target_title = resolve_week_title(service, target_date)
        else:
            target_date = datetime.utcnow().date()
            target_title = resolve_week_title(service, target_date)

        if not target_title:
            return jsonify({"error": "Target week not found"}), 404

        # === Fetch dinner range ===
        dinner_range = f"'{target_title}'!G20:H27"
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=dinner_range
        ).execute()
        rows = result.get("values", [])

        if not rows:
            return jsonify({"error": f"No data found in range {dinner_range}"}), 404

        # Expected structure: first col = Day (Mon–Sun), second col = Meal
        dinners = []
        for row in rows:
            if len(row) < 2:
                continue
            day = row[0].strip()
            meal = row[1].strip()
            if day and meal:
                dinners.append({"day": day, "meal": meal})

        print(f"✅ Dinner debug — target_title={target_title}, dinner_range={dinner_range}, rows={rows}")
        
        return jsonify({
            "week_commencing": target_title.replace("WC ", ""),
            "range": dinner_range,
            "meals": dinners
        }), 200

    except Exception as e:
        print(f"❌ Error in get_dinner: {e}")
        return jsonify({"error": str(e)}), 500
