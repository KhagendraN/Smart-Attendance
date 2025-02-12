import os

# google_service_account_info = os.environ.get('GOOGLE_SERVICE_ACCOUNT_INFO')
# print(google_service_account_info)  # Check if it prints the correct JSON string


from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = '/home/khagendra/Downloads/attendance-system-450401-68037343dc6d.json'
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)

SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID')


try:
    sheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    print("✅ Access successful! Spreadsheet title:", sheet["properties"]["title"])
except Exception as e:
    print("🚨 Error:", e)
