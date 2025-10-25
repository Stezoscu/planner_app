from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import os

# Google Sheets read/write scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet_service():
    creds = None
    token_path = "token.pickle"

    # Load saved credentials (if they exist)
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save credentials for next time
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    # Create the Sheets service
    service = build("sheets", "v4", credentials=creds)
    return service
