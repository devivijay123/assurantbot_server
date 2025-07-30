import logging
from fpdf import FPDF
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

from app.constants import PREAPPROVAL_FIELDS
import os, json

logger = logging.getLogger(__name__)
    

# SERVICE_ACCOUNT_FILE  = json.loads(os.getenv("GOOGLE_SHEET_CONFIG"))

# SERVICE_ACCOUNT_FILE = "./chat-bot-466011-31b3a06a5fd6.json"

SPREADSHEET_ID = "10J4xrgHPCRmEENtEtA_kuoTsvMOohfmIvV571i_VPIo"

SHEET_NAME = "Sheet1"  # Change if your sheet/tab name is different






# def write_preapproval_to_sheet(data):
#     try:
#         logger.info("Starting to write pre-approval data to Google Sheet.")
        
#         scopes = ["https://www.googleapis.com/auth/spreadsheets"]
#         creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=scopes)
#         client = gspread.authorize(creds)

#         logger.debug("Successfully authenticated with Google Sheets API.")

#         sheet = client.open_by_key(SPREADSHEET_ID)
#         worksheet = sheet.sheet1  # Or .worksheet("YourSheetName")
#         logger.debug("Opened spreadsheet and selected worksheet.")
#         # Prepare headers (questions)
#         headers = [field["question"] for field in PREAPPROVAL_FIELDS]

#         # Check if headers are already present (first row)
#         existing_headers = worksheet.row_values(1)

#         if not existing_headers:  # If sheet is empty, add headers
#             worksheet.insert_row(headers, 1)
#             logger.info("Headers added to Google Sheet.")
#         # Prepare row from data
#         row = [data.get(field["key"], "") for field in PREAPPROVAL_FIELDS]
#         logger.debug(f"Prepared row data: {row}")

#         worksheet.append_row(row)
#         logger.info("Data appended successfully to the Google Sheet.")

#         # Construct the spreadsheet link
#         spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0"
#         logger.info(f"Spreadsheet URL: {spreadsheet_url}")
        
#         return spreadsheet_url

#     except Exception as e:
#         logger.error(f"Error writing to spreadsheet: {e}", exc_info=True)
#         raise
def write_preapproval_to_sheet(data):
    try:
        logger.info("Starting to write pre-approval data to Google Sheet.")
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        service_account_info = json.loads(os.getenv("GOOGLE_SHEET_CONFIG"))
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = gspread.authorize(creds)

        sheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.sheet1

        # Add header row if sheet is empty
        if len(worksheet.get_all_values()) == 0:
            headers = [field["question"] for field in PREAPPROVAL_FIELDS]
            worksheet.append_row(headers)

        row = [data.get(field["key"], "") for field in PREAPPROVAL_FIELDS]
        worksheet.append_row(row)

        logger.info("Data appended successfully to the Google Sheet.")
        return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0"

    except Exception as e:
        logger.error(f"Error writing to spreadsheet: {e}", exc_info=True)
        raise

def generate_preapproval_pdf(data: dict, email: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Pre-Approval Submission", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Email: {email}", ln=True)

    for key, value in data.items():
        pdf.multi_cell(200, 10, txt=f"{key.replace('_', ' ').title()}: {value}")

    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Submitted: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", ln=True)

    filename = f"preapproval_{email.replace('@', '_at_')}.pdf"
    pdf.output(filename)
    return filename



