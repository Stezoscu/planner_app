from google_auth import get_gsheet_service
from datetime import datetime, timedelta
import re

# === CONFIG ===
SPREADSHEET_ID = "1DYUYj8ahyulNKYGGca91QtJIAykrYn_Tfa55qREAMkk"
TEMPLATE_SHEET_NAME = "Standard Week"
WEEK_PREFIX = "WC "  # naming convention e.g. WC 27/10/25

def parse_week_date(title):
    """Extract the date from a tab name like 'WC 20/10/25'"""
    match = re.search(r"WC (\d{1,2})/(\d{1,2})/(\d{2,4})", title)
    if not match:
        return None
    day, month, year = map(int, match.groups())
    year = 2000 + year if year < 100 else year
    return datetime(year, month, day).date()

def get_next_monday(latest_date):
    return latest_date + timedelta(days=7)

def generate_next_week():
    service = get_gsheet_service()

    # Get list of all sheets
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get("sheets", [])

    # Find the latest WC tab
    latest_date = None
    latest_sheet = None
    for s in sheets:
        title = s["properties"]["title"]
        week_date = parse_week_date(title)
        if week_date:
            if not latest_date or week_date > latest_date:
                latest_date = week_date
                latest_sheet = title

    if not latest_date:
        print("No weekly tabs found. Starting from today's Monday.")
        today = datetime.now().date()
        latest_date = today - timedelta(days=today.weekday())

    next_week = get_next_monday(latest_date)
    new_tab_title = f"{WEEK_PREFIX}{next_week.strftime('%d/%m/%y')}"

    # Check if tab already exists
    if any(s["properties"]["title"] == new_tab_title for s in sheets):
        print(f"Tab '{new_tab_title}' already exists — skipping.")
        return

    # Find the template tab ID
    template_tab = next((s for s in sheets if s["properties"]["title"] == TEMPLATE_SHEET_NAME), None)
    if not template_tab:
        raise ValueError(f"Template sheet '{TEMPLATE_SHEET_NAME}' not found!")

    template_id = template_tab["properties"]["sheetId"]

    # Duplicate the template tab
    duplicate_request = {
        "requests": [
            {
                "duplicateSheet": {
                    "sourceSheetId": template_id,
                    "insertSheetIndex": len(sheets),
                    "newSheetName": new_tab_title,
                }
            }
        ]
    }

    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body=duplicate_request
    ).execute()

    print(f"✅ Created new week tab: {new_tab_title}")

    # Update cell A1 in the new tab
    update_range = f"'{new_tab_title}'!A1"
    update_body = {
        "values": [["Week Commencing", next_week.strftime("%d/%m/%y")]]
    }

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption="RAW",
        body=update_body
    ).execute()

    print(f"🗓️ Set Week Commencing date in A1: {next_week.strftime('%d/%m/%y')}")

if __name__ == "__main__":
    generate_next_week()
