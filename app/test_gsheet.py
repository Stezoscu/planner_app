from google_auth import get_gsheet_service

# Replace with your Google Sheet ID
SHEET_ID = "1DYUYj8ahyulNKYGGca91QtJIAykrYn_Tfa55qREAMkk"

service = get_gsheet_service()
sheet = service.spreadsheets()

result = sheet.values().get(
    spreadsheetId=SHEET_ID,
    range="A1:C5"  # adjust to a real area of your sheet
).execute()

values = result.get("values", [])
print(values)
