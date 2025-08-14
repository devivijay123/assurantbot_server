import requests
import os
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("DOCUCLIPPER_API_KEY")
BASE_URL = "https://www.docuclipper.com/api/v1/protected"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

class DocuClipperError(Exception):
    """Custom exception for DocuClipper API errors"""
    pass

async def process_bank_statement(pdf_path: str) -> Optional[Dict[str, Any]]:
    """
    Uploads a PDF to DocuClipper, checks if it's a bank statement,
    and if yes, extracts and returns the bank statement data.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Optional[Dict[str, Any]]: Bank statement data if successful, None if not a bank statement
        
    Raises:
        DocuClipperError: If there's an API error or the PDF is encrypted
    """
    try:
        logger.info(f"Processing bank statement: {pdf_path}")
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            raise DocuClipperError(f"File not found: {pdf_path}")
        
        # ==== 1. UPLOAD DOCUMENT ====
        with open(pdf_path, "rb") as f:
            files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
            upload_resp = requests.post(
                f"{BASE_URL}/document?asyncProcessing=false",
                headers=HEADERS,
                files=files,
                timeout=30
            )

        logger.info(f"Upload response status: {upload_resp.status_code}")
        
        # Handle different status codes for upload
        if upload_resp.status_code == 201:
            # Document uploaded but may need processing
            upload_data = upload_resp.json()
            logger.info(f"Upload successful with 201: {upload_data}")
        elif upload_resp.status_code == 200:
            upload_data = upload_resp.json()
            logger.info(f"Upload successful with 200: {upload_data}")
        else:
            error_text = upload_resp.text
            logger.error(f"Upload failed: {upload_resp.status_code} {error_text}")
            raise DocuClipperError(f"Upload failed: {upload_resp.status_code} {error_text}")

        # Extract document UID from response
        document_uid = None
        if "document" in upload_data and "id" in upload_data["document"]:
            document_uid = upload_data["document"]["id"]
        elif "documentUid" in upload_data:
            document_uid = upload_data["documentUid"]
        elif "id" in upload_data:
            document_uid = upload_data["id"]
            
        if not document_uid:
            logger.error(f"No document UID found in response: {upload_data}")
            raise DocuClipperError("No document UID returned from upload.")

        logger.info(f"Document UID: {document_uid}")

        # Check for encryption
        encryption_status = ""
        if "pdfInfo" in upload_data and "properties" in upload_data["pdfInfo"]:
            encryption_status = upload_data["pdfInfo"]["properties"].get("encrypted", "").lower()
        elif "encrypted" in upload_data:
            encryption_status = upload_data.get("encrypted", "").lower()

        if "yes" in encryption_status:
            raise DocuClipperError("This PDF is encrypted. Please upload an unprotected version.")

        # ==== 2. CLASSIFY DOCUMENT ====
        classify_resp = requests.post(
            f"{BASE_URL}/document-classify",
            headers=HEADERS,
            json={"documentUid": document_uid},
            timeout=30
        )

        logger.info(f"Classification response status: {classify_resp.status_code}")

        if classify_resp.status_code != 200:
            error_text = classify_resp.text
            logger.error(f"Classification failed: {classify_resp.status_code} {error_text}")
            raise DocuClipperError(f"Classification failed: {classify_resp.status_code} {error_text}")

        classify_data = classify_resp.json()
        doc_type = classify_data.get("documentType", "").lower()
        
        logger.info(f"Document type: {doc_type}")

        if doc_type != "bank_statement":
            logger.info("Document is not a bank statement")
            return None

        # ==== 3. EXTRACT BANK STATEMENT DATA ====
        extract_resp = requests.post(
            f"{BASE_URL}/document-extract-bank-statement",
            headers=HEADERS,
            json={"documentUid": document_uid},
            timeout=60  # Bank statement extraction might take longer
        )

        logger.info(f"Extraction response status: {extract_resp.status_code}")

        if extract_resp.status_code != 200:
            error_text = extract_resp.text
            logger.error(f"Extraction failed: {extract_resp.status_code} {error_text}")
            raise DocuClipperError(f"Extraction failed: {extract_resp.status_code} {error_text}")

        extraction_data = extract_resp.json()
        logger.info("Bank statement data extracted successfully")
        
        return extraction_data

    except requests.exceptions.Timeout:
        logger.error("Request timeout while processing bank statement")
        raise DocuClipperError("Request timeout. Please try again.")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while processing bank statement")
        raise DocuClipperError("Connection error. Please check your internet connection.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise DocuClipperError(f"Request error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in process_bank_statement: {str(e)}")
        raise DocuClipperError(f"Unexpected error: {str(e)}")

def format_bank_statement_summary(bank_data: Dict[str, Any]) -> str:
    """
    Format bank statement data into a readable summary for chat response.
    
    Args:
        bank_data (Dict[str, Any]): Extracted bank statement data
        
    Returns:
        str: Formatted summary string
    """
    try:
        summary = "✅ **Bank Statement Processed Successfully**\n\n"
        
        # Basic account information
        if "accountInfo" in bank_data:
            account_info = bank_data["accountInfo"]
            if "bankName" in account_info:
                summary += f"🏦 **Bank:** {account_info['bankName']}\n"
            if "accountNumber" in account_info:
                # Mask account number for security
                account_num = account_info["accountNumber"]
                masked_num = "*" * (len(account_num) - 4) + account_num[-4:] if len(account_num) > 4 else account_num
                summary += f"💳 **Account:** {masked_num}\n"
            if "accountHolderName" in account_info:
                summary += f"👤 **Account Holder:** {account_info['accountHolderName']}\n"
        
        # Statement period
        if "statementPeriod" in bank_data:
            period = bank_data["statementPeriod"]
            if "startDate" in period and "endDate" in period:
                summary += f"📅 **Period:** {period['startDate']} to {period['endDate']}\n"
        
        # Balance information
        if "balances" in bank_data:
            balances = bank_data["balances"]
            if "openingBalance" in balances:
                summary += f"💰 **Opening Balance:** ${balances['openingBalance']:,.2f}\n"
            if "closingBalance" in balances:
                summary += f"💰 **Closing Balance:** ${balances['closingBalance']:,.2f}\n"
        
        # Transaction summary
        if "transactions" in bank_data and isinstance(bank_data["transactions"], list):
            transaction_count = len(bank_data["transactions"])
            summary += f"📊 **Transactions:** {transaction_count} found\n"
            
            # Calculate totals
            total_credits = sum(t.get("amount", 0) for t in bank_data["transactions"] if t.get("type") == "credit")
            total_debits = sum(abs(t.get("amount", 0)) for t in bank_data["transactions"] if t.get("type") == "debit")
            
            if total_credits > 0:
                summary += f"📈 **Total Credits:** ${total_credits:,.2f}\n"
            if total_debits > 0:
                summary += f"📉 **Total Debits:** ${total_debits:,.2f}\n"
        
        summary += "\n🎉 Your bank statement has been successfully processed and the data has been extracted for your pre-approval application."
        
        return summary
        
    except Exception as e:
        logger.error(f"Error formatting bank statement summary: {str(e)}")
        return "✅ Bank statement processed successfully. Data has been extracted for your pre-approval application."

async def process_multiple_bank_statements(uploaded_files_info: list, user_email: str) -> dict:
    """
    Process multiple uploaded files and validate them as bank statements.
    
    Args:
        uploaded_files_info (list): List of uploaded file information
        user_email (str): User's email for logging
        
    Returns:
        dict: Processing results with success status, processed statements, and error messages
    """
    processed_statements = []
    validation_errors = []
    
    logger.info(f"Processing {len(uploaded_files_info)} files for user {user_email}")
    
    for file_info in uploaded_files_info:
        file_path = file_info["file_path"]
        filename = file_info['original_filename']
        
        logger.info(f"🔍 Checking file: {filename} at {file_path}")
        
        try:
            # Validate and process bank statement
            is_valid, error_msg, extracted_data = await validate_bank_statement_file(file_path)
            
            if not is_valid:
                validation_errors.append(f"❌ **{filename}**: {error_msg}")
                logger.warning(f"File {filename} failed validation: {error_msg}")
            else:
                processed_statements.append({
                    "filename": filename,
                    "data": extracted_data,
                    "file_info": file_info
                })
                logger.info(f"✅ Successfully processed: {filename}")
                
        except Exception as e:
            error_message = f"Error processing file - {str(e)}"
            logger.error(f"Error processing {filename}: {str(e)}")
            validation_errors.append(f"❌ **{filename}**: {error_message}")
    
    # Determine success status
    success = len(processed_statements) > 0
    
    # Create response message
    if validation_errors and not processed_statements:
        # All files failed
        error_message = "None of the uploaded files could be processed:\n\n" + "\n".join(validation_errors)
        error_message += "\n\n📋 Please upload valid bank statement files (PDF format recommended) to continue."
        return {
            "success": False,
            "error_message": error_message,
            "processed_statements": [],
            "validation_errors": validation_errors
        }
    elif validation_errors and processed_statements:
        # Some files failed, some succeeded
        warning_message = "Some files could not be processed:\n\n" + "\n".join(validation_errors)
        warning_message += "\n\n📋 Please upload valid bank statement files for the failed items."
        return {
            "success": True,
            "warning_message": warning_message,
            "processed_statements": processed_statements,
            "validation_errors": validation_errors
        }
    else:
        # All files succeeded
        return {
            "success": True,
            "processed_statements": processed_statements,
            "validation_errors": []
        }

def create_bank_statement_response(processing_result: dict) -> dict:
    """
    Create a formatted response message for bank statement processing results.
    
    Args:
        processing_result (dict): Result from process_multiple_bank_statements
        
    Returns:
        dict: Formatted response with message and processed data
    """
    if not processing_result["success"]:
        return {
            "reply": processing_result["error_message"],
            "processed_data": None
        }
    
    processed_statements = processing_result["processed_statements"]
    file_names = [stmt["filename"] for stmt in processed_statements]
    
    # Create summary of processed statements
    summary_parts = []
    for stmt in processed_statements:
        if stmt["data"]:
            summary = format_bank_statement_summary(stmt["data"])
            summary_parts.append(f"**{stmt['filename']}**\n{summary}")
    
    # Build response message
    response_message = f"✅ **Bank Statement(s) Processed Successfully!**\n\n"
    response_message += f"📁 **Files processed:** {', '.join(file_names)}\n\n"
    
    if summary_parts:
        response_message += "📊 **Summary:**\n" + "\n\n".join(summary_parts) + "\n\n"
    
    # Add warning if some files failed
    if processing_result.get("warning_message"):
        response_message += f"⚠️ **Warning:**\n{processing_result['warning_message']}\n\n"
    
    return {
        "reply": response_message,
        "processed_data": {
            "files": [stmt["file_info"] for stmt in processed_statements],
            "extracted_data": [stmt["data"] for stmt in processed_statements]
        }
    }

async def validate_bank_statement_file(file_path: str) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate if a file is a bank statement and extract data if it is.
    
    Args:
        file_path (str): Path to the file to validate
        
    Returns:
        tuple[bool, Optional[str], Optional[Dict[str, Any]]]: 
            (is_valid, error_message, extracted_data)
    """
    try:
        extracted_data = await process_bank_statement(file_path)
        
        if extracted_data is None:
            return False, "This file does not appear to be a bank statement. Please upload a valid bank statement.", None
        
        return True, None, extracted_data
        
    except DocuClipperError as e:
        logger.error(f"DocuClipper error validating bank statement: {str(e)}")
        return False, f"Error processing bank statement: {str(e)}", None
    except Exception as e:
        logger.error(f"Unexpected error validating bank statement: {str(e)}")
        return False, "An unexpected error occurred while processing your bank statement. Please try again.", None