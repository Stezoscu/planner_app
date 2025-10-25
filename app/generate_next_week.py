from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import json
from datetime import datetime, timedelta


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/spreadsheets"]

# --- Google Auth Helper ---
def get_gsheet_service():
    creds = None

    # Try token.json first (used in CI)
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid creds, use OAuth flow (local dev)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Only used for local runs, not GitHub Actions
            if os.path.exists("client_secret.json"):
                flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise RuntimeError("No valid credentials or client_secret.json found")

        # Save the credentials locally
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


# --- Generate Next Week ---
def generate_next_week():
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise RuntimeError("Missing SHEET_ID environment variable")

    service = get_gsheet_service()
    sheet = service.spreadsheets()

    # Get all sheet metadata
    sheet_metadata = sheet.get(spreadsheetId=sheet_id).execute()
    sheets = sheet_metadata.get("sheets", [])

    # Find the "Standard Week" sheet
    template = next((s for s in sheets if s["properties"]["title"] == "Standard Week"), None)
    if not template:
        raise RuntimeError("Could not find sheet named 'Standard Week'")

    # Find the last "WC ..." sheet
    existing_wc_sheets = [
        s["properties"]["title"] for s in sheets if s["properties"]["title"].startswith("WC ")
    ]

    if existing_wc_sheets:
        latest_date = max([
            datetime.strptime(title.split(" ")[1], "%d/%m/%y") for title in existing_wc_sheets
        ])
        next_monday = latest_date + timedelta(days=7)
    else:
        next_monday = datetime.today() + timedelta(days=(7 - datetime.today().weekday()))

    new_title = f"WC {next_monday.strftime('%d/%m/%y')}"

    # Duplicate the template sheet
    body = {
        "requests": [
            {
                "duplicateSheet": {
                    "sourceSheetId": template["properties"]["sheetId"],
                    "insertSheetIndex": len(sheets),
                    "newSheetName": new_title
                }
            }
        ]
    }

    service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
    print(f"✅ Successfully created new sheet: {new_title}")


if __name__ == "__main__":
    generate_next_week()
