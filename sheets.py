# from google.oauth2.credentials import Credentials
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# import pandas as pd
# from datetime import datetime
# import json
# import os

# class GoogleSheetsManager:
#     def __init__(self):
#         self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
#         self.SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID')

#     def get_service(self):
#         creds_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT_INFO', '{}'))
#         if not creds_info:
#             raise ValueError("Google service account credentials not found")

#         creds = service_account.Credentials.from_service_account_info(
#             creds_info, scopes=self.SCOPES
#         )

#         return build('sheets', 'v4', credentials=creds)

#     def update_attendance(self, class_id, date, attendance_data):
#         service = self.get_service()
#         sheet = service.spreadsheets()

#         # Format data for sheets
#         values = [[
#             date.strftime('%Y-%m-%d'),
#             str(record['student_id']),
#             record['student_name'],
#             'Present' if record['status'] else 'Absent'
#         ] for record in attendance_data]

#         body = {
#             'values': values
#         }

#         # Create a new sheet for the class if it doesn't exist
#         spreadsheet = sheet.get(spreadsheetId=self.SPREADSHEET_ID).execute()
#         sheet_title = f'Class_{class_id}'

#         # Check if sheet exists
#         sheet_exists = any(s['properties']['title'] == sheet_title for s in spreadsheet.get('sheets', []))

#         if not sheet_exists:
#             requests = [{
#                 'addSheet': {
#                     'properties': {
#                         'title': sheet_title,
#                         'gridProperties': {
#                             'rowCount': 1000,
#                             'columnCount': 4
#                         }
#                     }
#                 }
#             }]
#             body = {'requests': requests}
#             service.spreadsheets().batchUpdate(
#                 spreadsheetId=self.SPREADSHEET_ID,
#                 body=body
#             ).execute()

#             # Add headers
#             headers = [['Date', 'Student ID', 'Student Name', 'Status']]
#             sheet.values().update(
#                 spreadsheetId=self.SPREADSHEET_ID,
#                 range=f'{sheet_title}!A1:D1',
#                 valueInputOption='RAW',
#                 body={'values': headers}
#             ).execute()

#         # Append attendance data
#         sheet.values().append(
#             spreadsheetId=self.SPREADSHEET_ID,
#             range=f'{sheet_title}!A:D',
#             valueInputOption='RAW',
#             body=body
#         ).execute()

#     def get_attendance_report(self, class_id, start_date, end_date):
#         service = self.get_service()
#         sheet = service.spreadsheets()

#         result = sheet.values().get(
#             spreadsheetId=self.SPREADSHEET_ID,
#             range=f'Class_{class_id}!A:D'
#         ).execute()

#         values = result.get('values', [])
#         if not values:
#             return pd.DataFrame(columns=['Date', 'Student ID', 'Student Name', 'Status'])

#         df = pd.DataFrame(values[1:], columns=values[0])

#         # Filter by date range
#         df['Date'] = pd.to_datetime(df['Date'])
#         mask = (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))
#         return df[mask]

#     def download_attendance_sheet(self, class_id, start_date, end_date):
#         """Generate Excel file with attendance data"""
#         df = self.get_attendance_report(class_id, start_date, end_date)

#         # Create a BytesIO object to store the Excel file
#         output = pd.ExcelWriter(f'attendance_report_{class_id}.xlsx', engine='openpyxl')
#         df.to_excel(output, index=False, sheet_name='Attendance')
#         output.save()

#         return f'attendance_report_{class_id}.xlsx'

from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime
import json
import os

class GoogleSheetsManager:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID')

    def get_service(self):
        creds_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT_INFO', '{}'))
        if not creds_info:
            raise ValueError("Google service account credentials not found")

        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=self.SCOPES
        )

        return build('sheets', 'v4', credentials=creds)

    def update_attendance(self, class_id, date, attendance_data):
        service = self.get_service()
        sheet = service.spreadsheets()

        # Format data for sheets
        values = [[
            date.strftime('%Y-%m-%d'),
            str(record['student_id']),
            record['student_name'],
            'Present' if record['status'] else 'Absent'
        ] for record in attendance_data]

        sheet_title = f'Class_{class_id}'

        # Check if the sheet exists
        spreadsheet = sheet.get(spreadsheetId=self.SPREADSHEET_ID).execute()
        sheet_exists = any(s['properties']['title'] == sheet_title for s in spreadsheet.get('sheets', []))

        if not sheet_exists:
            # Create a new sheet for the class
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': sheet_title,
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 4
                        }
                    }
                }
            }]
            service.spreadsheets().batchUpdate(
                spreadsheetId=self.SPREADSHEET_ID,
                body={'requests': requests}
            ).execute()

            # Add headers to the new sheet
            headers = [['Date', 'Student ID', 'Student Name', 'Status']]
            sheet.values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f'{sheet_title}!A1:D1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()

        # Append attendance data (Fix: Use correct JSON payload)
        sheet.values().append(
            spreadsheetId=self.SPREADSHEET_ID,
            range=f'{sheet_title}!A:D',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',  # Ensures new rows are added
            body={'values': values}  # Fixed: Correct payload structure
        ).execute()

    def get_attendance_report(self, class_id, start_date, end_date):
        service = self.get_service()
        sheet = service.spreadsheets()

        result = sheet.values().get(
            spreadsheetId=self.SPREADSHEET_ID,
            range=f'Class_{class_id}!A:D'
        ).execute()

        values = result.get('values', [])
        if not values:
            return pd.DataFrame(columns=['Date', 'Student ID', 'Student Name', 'Status'])

        df = pd.DataFrame(values[1:], columns=values[0])

        # Filter by date range
        df['Date'] = pd.to_datetime(df['Date'])
        mask = (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))
        return df[mask]

    def download_attendance_sheet(self, class_id, start_date, end_date):
        """Generate Excel file with attendance data"""
        df = self.get_attendance_report(class_id, start_date, end_date)

        # Create a BytesIO object to store the Excel file
        output = pd.ExcelWriter(f'attendance_report_{class_id}.xlsx', engine='openpyxl')
        df.to_excel(output, index=False, sheet_name='Attendance')
        output.save()

        return f'attendance_report_{class_id}.xlsx'
