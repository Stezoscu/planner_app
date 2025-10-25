import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet_service():
    creds = None
    token_path = "token.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
        # Save locally and also print it for GitHub setup
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        print("\n✅ Token saved to token.json")
        print("👇 Copy the following string into a GitHub secret called `GOOGLE_OAUTH_TOKEN`:\n")
        print(creds.to_json())

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("sheets", "v4", credentials=creds)
    return service
