"""Upload DataFrames to Google Sheets via OAuth."""

import os

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_gspread_client(credentials_file, token_file):
    """Return an authorized gspread client, launching browser login if needed."""
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return gspread.authorize(creds)


def upload_to_google_sheets(df, spreadsheet_id, tab_name, credentials_file, token_file):
    """Clear a Google Sheets tab and write the DataFrame into it."""
    client = _get_gspread_client(credentials_file, token_file)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=50)

    worksheet.clear()
    data = [df.columns.tolist()] + df.fillna("").values.tolist()
    worksheet.update(data, value_input_option="USER_ENTERED")
