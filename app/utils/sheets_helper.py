import os
from datetime import date, timedelta
from app.google_auth import get_gsheet_service


def get_current_week_tab(service, spreadsheet_id: str) -> str:
    """Find the tab name for the current week (e.g. 'WC 21/10/25')."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    expected_name = f"WC {monday.strftime('%d/%m/%y')}"
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    tab_names = [s["properties"]["title"] for s in metadata.get("sheets", [])]

    if expected_name in tab_names:
        return expected_name
    raise ValueError(f"No sheet tab found for {expected_name}")


def read_current_week_data(spreadsheet_id: str):
    """Read the range A1:O25 from the current week tab."""
    service = get_gsheet_service()
    tab = get_current_week_tab(service, spreadsheet_id)
    range_name = f"{tab}!A1:O25"  # adjust range if needed
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return {
        "tab": tab,
        "values": result.get("values", []),
    }
