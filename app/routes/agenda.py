from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from ..firebase_utils import firebase_required
from ..google_auth import get_gsheet_service
import os
import re

agenda_bp = Blueprint("agenda", __name__)

SPREADSHEET_ID = os.getenv("SHEET_ID")
TEMPLATE_SHEET = "Standard Week"

# Keep this mapping in one place if you prefer (same as in sheets.py/dinner.py)
USER_MAP = {
    "stephen@oldfamily.co.uk": "Steve",
    "house@oldfamily.co.uk": "Becky",
}

WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def resolve_week_title(service, target_date):
    """
    Find the 'WC dd/mm/yy' sheet whose week contains target_date.
    """
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

    for wc_date, title in sorted(week_sheets):
        if wc_date <= target_date <= wc_date + timedelta(days=6):
            return title

    return None


@agenda_bp.route("/", methods=["GET"])
@firebase_required
def get_agenda():
    """
    Returns the agenda for the authenticated user for a given day.
    Assumes the sheet structure:
      Row 1: Week Commencing / Notes
      Row 2: Day names repeated per 2 columns (e.g., Monday, Monday, Tuesday, Tuesday, ...)
      Row 3: 'Steve', 'Becky', 'Steve', 'Becky', ...
      Row 4+: Activity rows in col A; values under each (day, person) column.

    Query params:
      - date=YYYY-MM-DD  (preferred)
      - week=WC dd/mm/yy (optional, overrides date)
      - list=1           (optional: lists available WC sheets)
    """
    try:
        if not SPREADSHEET_ID:
            return jsonify({"error": "SHEET_ID not configured"}), 400

        service = get_gsheet_service()

        # list mode
        if request.args.get("list") == "1":
            ss = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            week_titles = [
                s["properties"]["title"]
                for s in ss.get("sheets", [])
                if s["properties"]["title"].startswith("WC ")
            ]
            week_titles.sort()
            return jsonify({"available_weeks": week_titles, "count": len(week_titles)}), 200

        # who is the user? (Steve/Becky)
        email = (request.user.get("email") or "").lower()
        person = USER_MAP.get(email)
        if not person:
            return jsonify({"error": f"No sheet user mapping for {email}"}), 403

        # which date/week?
        date_param = request.args.get("date")
        week_param = request.args.get("week")

        if week_param:
            target_title = week_param
            # If date wasn't supplied, use the "week commencing" date from the title for day-name purposes
            target_date = None
        else:
            if not date_param:
                return jsonify({"error": "Missing 'date' (YYYY-MM-DD)"}), 400
            try:
                target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid 'date'. Use YYYY-MM-DD."}), 400
            target_title = resolve_week_title(service, target_date)

        if not target_title:
            return jsonify({"error": "Target week not found"}), 404

        # Pull the sheet data
        # A1:Z200 is generous; adjust up/down if your sheet grows
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{target_title}'!A1:Z200",
        ).execute()
        rows = result.get("values", [])

        if len(rows) < 4:
            return jsonify({"error": f"Invalid structure in '{target_title}'"}), 500

        # Header rows
        # rows[1] -> days header (repeating day names across)
        # rows[2] -> person header ('Steve','Becky', repeating)
        days_header = rows[1]
        people_header = rows[2] if len(rows) > 2 else []

        # Determine which day to show:
        # From ?date -> weekday name; else default to Sunday (or any day if you decide)
        if target_date:
            weekday_name = WEEK_DAYS[target_date.weekday()]  # Monday..Sunday
        else:
            # If only ?week= was given and no date, default to today's weekday
            today = datetime.utcnow().date()
            weekday_name = WEEK_DAYS[today.weekday()]

        # Find the column that matches (weekday_name, person)
        # Remember column 0 is the activity name, so day/person columns start at index 1
        def find_user_col_for_day(day_name: str, person_name: str):
            # Build pairs: [(day_name, person_name, col_index)]
            # The sheet has repeating (Steve, Becky) for each day
            # e.g. days_header = ['', 'Monday', 'Monday', 'Tuesday', 'Tuesday', ...]
            #      people_header = ['', 'Steve', 'Becky', 'Steve', 'Becky', ...]
            for col in range(1, max(len(days_header), len(people_header))):
                d = days_header[col] if col < len(days_header) else ""
                p = people_header[col] if col < len(people_header) else ""
                if (d or "").strip() == day_name and (p or "").strip() == person_name:
                    return col
            return None

        user_col = find_user_col_for_day(weekday_name, person)
        if user_col is None:
            # As a fallback, check if headers might be shifted by 1 and day/person pattern is (day, day, person, person)
            # but the sheet you shared should match the (day, day) + (Steve, Becky) pattern. If not found, bail.
            return jsonify({"error": f"Could not locate column for {weekday_name}/{person}"}), 500

        # Build agenda items from data rows (rows[3:] onward)
        items = []
        for r in rows[3:]:
            if not r or not r[0]:
                continue
            activity = (r[0] or "").strip()
            value = (r[user_col] if len(r) > user_col else "").strip()
            # Skip empty values so your UI doesn't show blanks
            if value:
                items.append({
                    "title": activity,
                    "value": value,
                })

        # Optional: helpful debug
        print(f"✅ Agenda debug — user={person}, day={weekday_name}, sheet='{target_title}', user_col={user_col}, items={len(items)}")

        return jsonify({
            "week": target_title,
            "date": date_param or None,
            "day": weekday_name,
            "user": person,
            "items": items,
        }), 200

    except Exception as e:
        print(f"❌ Error in get_agenda: {e}")
        return jsonify({"error": str(e)}), 500
