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

    # --- Case 1: Use local token if present ---
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # --- Case 2: Use environment variables in CI (GitHub Actions) ---
    elif os.getenv("GOOGLE_OAUTH_TOKEN"):
        creds_json = os.getenv("GOOGLE_OAUTH_TOKEN")
        creds = Credentials.from_authorized_user_info(json.loads(creds_json), SCOPES)

    # --- Case 3: Run interactive OAuth flow locally ---
    else:
        # Prefer local file if available, else fallback to env var
        if os.path.exists("client_secret.json"):
            client_secret_file = "client_secret.json"
        elif os.getenv("GOOGLE_CLIENT_SECRET"):
            # write to a temporary file to support InstalledAppFlow
            with open("client_secret_temp.json", "w") as f:
                f.write(os.getenv("GOOGLE_CLIENT_SECRET"))
            client_secret_file = "client_secret_temp.json"
        else:
            raise FileNotFoundError("No client_secret.json or GOOGLE_CLIENT_SECRET found")

        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save locally for reuse
        with open(token_path, "w") as token:
            token.write(creds.to_json())

        print("\n✅ Token saved to token.json")
        print("👇 Copy the following string into GitHub Secret `GOOGLE_OAUTH_TOKEN`:\n")
        print(creds.to_json())

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("sheets", "v4", credentials=creds)
