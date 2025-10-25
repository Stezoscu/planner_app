from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
import json

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet_service():
    # Use credentials from the GOOGLE_SHEETS_CREDENTIALS env variable
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

    if not creds_json:
        raise ValueError("Missing GOOGLE_SHEETS_CREDENTIALS environment variable")

    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

    service = build("sheets", "v4", credentials=creds)
    return service
