from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from ..google_auth import get_gsheet_service
from ..firebase_utils import firebase_required
import re
import os

sheets_bp = Blueprint("sheets", __name__)

SPREADSHEET_ID = os.getenv("SHEET_ID")
TEMPLATE_SHEET = "Standard Week"

# === Firebase email → sheet name mapping ===
USER_MAP = {
    "stephen@oldfamily.co.uk": "Steve",
    "house@oldfamily.co.uk": "Becky",
}


# --- Ensure target week sheet exists (create from template if needed) ---
def ensure_week_exists(service, spreadsheet_id: str, base_date: datetime, weeks_ahead: int, template_title: str = "Standard Week"):
    """Ensure the requested week exists, creating it from the template if needed."""
    target_date = base_date + timedelta(days=7 * weeks_ahead)
    new_title = f"WC {target_date.day:02d}/{target_date.month:02d}/{str(target_date.year)[2:]}"
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    titles = {s["properties"]["title"]: s["properties"]["sheetId"] for s in ss.get("sheets", [])}

    if new_title in titles:
        print(f"🟢 Sheet '{new_title}' already exists, skipping creation.")
        return {"created": False, "title": new_title}

    if template_title not in titles:
        warning_msg = f"⚠️ Template '{template_title}' not found — cannot create '{new_title}'."
        print(warning_msg)
        return {"created": False, "title": new_title, "warning": warning_msg}

    template_sheet_id = titles[template_title]
    body = {
        "requests": [{
            "duplicateSheet": {
                "sourceSheetId": template_sheet_id,
                "insertSheetIndex": len(titles),
                "newSheetName": new_title
            }
        }]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    # Stamp B1 with week commencing date
    week_commencing = f"{target_date.day:02d}/{target_date.month:02d}/{str(target_date.year)[2:]}"
    try:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{new_title}'!B1",
            valueInputOption="RAW",
            body={"values": [[week_commencing]]}
        ).execute()
    except Exception:
        pass  # Not critical if B1 update fails

    print(f"✅ Created new sheet: {new_title} ({weeks_ahead} week(s) from base)")
    return {"created": True, "title": new_title}


# === GET WEEK DATA ===
@sheets_bp.route("/current_week", methods=["GET"])
@firebase_required
def current_week():
    """
    Returns structured data for a given week tab.
    Query params:
      - offset: integer (e.g. -1 = last week, 0 = current, 1 = next)
      - week=WC dd/mm/yy → directly select a week
      - list=1 → lists all WC sheets
    """
    try:
        if not SPREADSHEET_ID:
            return jsonify({"error": "SHEET_ID not configured"}), 400

        # --- Firebase user info ---
        firebase_user = request.user
        user_email = firebase_user.get("email", "").lower()
        sheet_name = USER_MAP.get(user_email, "Unknown")
        print(f"👤 Logged in as {user_email} → viewing sheet section for {sheet_name}")

        service = get_gsheet_service()
        ss = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()

        # Extract all WC sheets
        weeks = []
        for s in ss.get("sheets", []):
            title = s["properties"]["title"]
            match = re.search(r"WC\s(\d{1,2})/(\d{1,2})/(\d{2,4})", title)
            if match:
                d, m, y = map(int, match.groups())
                if y < 100:
                    y += 2000
                weeks.append((datetime(y, m, d), title))

        if not weeks:
            return jsonify({"error": "No 'WC dd/mm/yy' sheets found"}), 404

        weeks.sort(key=lambda w: w[0])
        all_titles = [t for _, t in weeks]
        latest_date, latest_title = weeks[-1]

        # --- Handle ?list=1 ---
        if request.args.get("list") == "1":
            return jsonify({
                "available_weeks": all_titles,
                "latest": latest_title,
                "count": len(all_titles)
            })

        # --- Determine which week to load ---
        offset = request.args.get("offset")
        week_param = request.args.get("week")
        target_title = None
        meta = {"created": False, "title": None}

        if week_param:  # Direct lookup
            week_param = week_param.strip()
            if week_param in all_titles:
                target_title = week_param
            else:
                return jsonify({"error": f"Week '{week_param}' not found", "available": all_titles}), 404
        else:  # Offset logic
            offset = int(offset or 0)
            target_date = latest_date + timedelta(days=7 * offset)
            for dt, title in weeks:
                if dt == target_date:
                    target_title = title
                    break
            if not target_title:
                if offset >= 1:
                    meta = ensure_week_exists(service, SPREADSHEET_ID, latest_date, offset, TEMPLATE_SHEET)
                    target_title = meta["title"]
                else:
                    return jsonify({
                        "error": f"Requested week (offset={offset}) not found",
                        "available": all_titles
                    }), 404

        # --- Fetch values ---
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{target_title}'!A1:Z50"
        ).execute()

        rows = result.get("values", [])
        if len(rows) < 4:
            return jsonify({"error": f"Invalid structure in '{target_title}'"}), 500

        # --- Parse sheet structure ---
        days = rows[1][1:]
        week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        structured = {
            "week_commencing": target_title.replace("WC ", ""),
            "days": {day: {"Steve": {}, "Becky": {}} for day in week_order},
            "user_view": sheet_name,
            "_meta": meta
        }

        # Map columns
        day_pairs = []
        for i in range(0, len(days), 2):
            day_name = days[i]
            if day_name in week_order:
                day_pairs.append((day_name, i))

        # Fill structured data
        for r in rows[3:]:
            if not r or not r[0]:
                continue
            activity = r[0]
            for day_name, base_col in day_pairs:
                steve_val = r[base_col + 1] if len(r) > base_col + 1 else ""
                becky_val = r[base_col + 2] if len(r) > base_col + 2 else ""
                structured["days"][day_name]["Steve"][activity] = steve_val or "N/A"
                structured["days"][day_name]["Becky"][activity] = becky_val or "N/A"

        # --- Filter to logged-in user's section only ---
        filtered = {
            "week_commencing": structured["week_commencing"],
            "person": sheet_name,
            "days": {
                day: structured["days"][day][sheet_name] for day in week_order
            },
            "_meta": structured["_meta"]
        }

        print(f"📆 Returned structured data for '{target_title}' ({sheet_name}, offset/param={offset or week_param})")
        return jsonify(filtered)

    except Exception as e:
        print(f"❌ Error loading week data: {e}")
        return jsonify({"error": str(e)}), 500


# === MANAGE SHEETS (LIST, CREATE, DELETE OLD) ===
@sheets_bp.route("/api/sheets/manage", methods=["GET", "POST", "DELETE"])
def manage_sheets():
    """
    Manage week tabs in the Google Sheet.
    - GET: list all 'WC dd/mm/yy' tabs
    - POST: create a new week tab (?offset=2 creates two weeks ahead)
    - DELETE: remove old tabs (?keep_weeks=8 keeps last 8 weeks)
    """
    try:
        service = get_gsheet_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get("sheets", [])

        week_tabs = []
        for s in sheets:
            title = s["properties"]["title"]
            match = re.search(r"WC\s(\d{1,2})/(\d{1,2})/(\d{2,4})", title)
            if match:
                d, m, y = map(int, match.groups())
                if y < 100:
                    y += 2000
                week_tabs.append({
                    "title": title,
                    "date": datetime(y, m, d),
                    "sheetId": s["properties"]["sheetId"]
                })

        week_tabs.sort(key=lambda w: w["date"])
        latest_date = week_tabs[-1]["date"] if week_tabs else datetime.today()

        # === GET ===
        if request.method == "GET":
            return jsonify({
                "count": len(week_tabs),
                "weeks": [
                    {
                        "title": w["title"],
                        "week_commencing": w["date"].strftime("%d/%m/%y")
                    }
                    for w in week_tabs
                ]
            })

        # === POST ===
        elif request.method == "POST":
            offset = int(request.args.get("offset", 1))
            result = ensure_week_exists(
                service=service,
                spreadsheet_id=SPREADSHEET_ID,
                base_date=latest_date,
                weeks_ahead=offset,
                template_title=TEMPLATE_SHEET
            )

            if "warning" in result:
                return jsonify(result), 400

            return jsonify({
                "message": f"Created week tab: {result['title']}" if result["created"] else f"Week '{result['title']}' already exists",
                "result": result
            }), 201 if result["created"] else 200

        # === DELETE ===
        elif request.method == "DELETE":
            keep_weeks = int(request.args.get("keep_weeks", 8))
            cutoff_date = datetime.today() - timedelta(weeks=keep_weeks)

            to_delete = [w for w in week_tabs if w["date"] < cutoff_date and w["title"] != TEMPLATE_SHEET]
            delete_requests = [{"deleteSheet": {"sheetId": w["sheetId"]}} for w in to_delete]

            if not delete_requests:
                return jsonify({"message": f"No sheets older than {keep_weeks} weeks found."}), 200

            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"requests": delete_requests}
            ).execute()

            deleted_titles = [w["title"] for w in to_delete]
            print(f"🧹 Deleted {len(deleted_titles)} old sheets: {deleted_titles}")
            return jsonify({
                "message": f"Deleted {len(deleted_titles)} old sheets.",
                "deleted": deleted_titles
            }), 200

    except Exception as e:
        print(f"❌ Error in manage_sheets: {e}")
        return jsonify({"error": str(e)}), 500
