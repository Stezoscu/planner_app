from flask import Blueprint, jsonify
from datetime import datetime
from ..google_auth import get_gsheet_service
import re

sheets_bp = Blueprint("sheets", __name__)

SPREADSHEET_ID = "https://www.googleapis.com/auth/spreadsheets"
TEMPLATE_SHEET = "Standard Week"

@sheets_bp.route("/api/sheets/auto_week", methods=["POST"])
def auto_generate_next_week():
    """Duplicate the 'Standard Week' tab and rename to WC dd/mm/yy for next week"""
    try:
        service = get_gsheet_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get("sheets", [])

        # --- find existing WC sheets ---
        wc_sheets = []
        for s in sheets:
            title = s["properties"]["title"]
            match = re.search(r"WC\s(\d{1,2})/(\d{1,2})/(\d{2,4})", title)
            if match:
                day, month, year = map(int, match.groups())
                year = 2000 + year if year < 100 else year
                wc_sheets.append(datetime(year, month, day))
        
        latest_date = max(wc_sheets) if wc_sheets else datetime.today()
        next_week_date = latest_date + timedelta(days=7)
        new_title = f"WC {next_week_date.day:02d}/{next_week_date.month:02d}/{str(next_week_date.year)[2:]}"

        # --- prevent creating more than 2 weeks ahead ---
        if (next_week_date - datetime.today()).days > 14:
            return jsonify({"message": "Already 2+ weeks ahead — skipping"}), 200

        # --- duplicate Standard Week sheet ---
        template_sheet_id = next(
            s["properties"]["sheetId"] for s in sheets if s["properties"]["title"] == TEMPLATE_SHEET
        )

        duplicate_request = {
            "requests": [{
                "duplicateSheet": {
                    "sourceSheetId": template_sheet_id,
                    "insertSheetIndex": len(sheets),
                    "newSheetName": new_title
                }
            }]
        }

        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=duplicate_request
        ).execute()

        return jsonify({"message": f"Created new sheet: {new_title}"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
