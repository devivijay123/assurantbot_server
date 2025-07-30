from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from collections import defaultdict
from app.models import ChatInput
from app.database import chat_collection, pre_approvals_collection
from openai import OpenAI
import os
import requests
from bs4 import BeautifulSoup
import asyncio
import logging
from app.pdf_generator import generate_preapproval_pdf
from app.email_service import send_client_notification_with_attachments, send_email_with_attachment, send_email_with_multiple_attachments
from app.pdf_generator import write_preapproval_to_sheet  
from app.constants import PREAPPROVAL_FIELDS, SYSTEM_PROMPT, EMAIL_BODY
import aiofiles 
from typing import Optional,  List
import uuid
from pathlib import Path

load_dotenv()
CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
datetime.utcnow()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
message_histories = defaultdict(list)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types for bank statements
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB



@router.get("/")
async def root():
    return {"message": "Chaat API"}


#state management
user_states = defaultdict(lambda: {
    "preapproval_started": False,
    "current_question_index": -1,
    "answers": {},
    "uploaded_files": []
})
async def save_uploaded_file(file: UploadFile, user_email: str) -> dict:
    """Save uploaded file and return file info"""
    try:
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Please upload PDF, JPG, JPEG, or PNG files only."
            )
        
        # Validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE/1024/1024}MB"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Store file info in database
        file_info = {
            "original_filename": file.filename,
            "stored_filename": unique_filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "file_type": file_extension,
            "upload_time": datetime.utcnow(),
            "user_email": user_email
        }
        
        # Insert file info into database
        chat_collection.insert_one({
            "email": user_email,
            "file_info": file_info,
            "sender": "user",
            "message_type": "file_upload",
            "timestamp": datetime.utcnow()
        })
        
        logger.info(f"File uploaded successfully: {file.filename} for user {user_email}")
        return file_info
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

def get_mortgage_rates():
    url = "https://www.mortgagenewsdaily.com/mortgage-rates"
    response = requests.get(url)
    print("Fetched URL status:", response.status_code)

    soup = BeautifulSoup(response.content, "html.parser")
    print("Soup created")

    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables")
    for i, table in enumerate(tables):
        print(f"Table {i} class: {table.get('class')}")

    # Updated selector based on class
    rates = {}
    for table in soup.find_all("table", class_="mtg-rates"):
        rows = table.find_all("tr")
        print(f"Found {len(rows)} rows in table.mtg-rates")

        for i, row in enumerate(rows[1:], start=1):
            cols = row.find_all("td")
            print(f"Row {i}: {len(cols)} columns")

            if len(cols) >= 2:
                rate_type = cols[0].text.strip()
                rate_value = cols[1].text.strip()
                print(f"Rate Type: {rate_type}, Rate Value: {rate_value}")
                rates[rate_type] = rate_value

    print("Final rates dictionary:", rates)
    return rates

def get_fannie_mae_summary():
    url = "https://selling-guide.fanniemae.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
        return "\n\n".join(text_blocks[:2]) if text_blocks else "No content extracted."
    except Exception as e:
        return f"Failed to fetch: {str(e)}"


def get_freddie_mac_summary():
    url = "https://guide.freddiemac.com/app/guide/browse"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
        return "\n\n".join(text_blocks[:2]) if text_blocks else "No content extracted."
    except Exception as e:
        return f"Failed to fetch: {str(e)}"


def get_hud_fha_summary():
    url = "https://www.hud.gov/hud-partners/single-family-fha-resource-center"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
        return "\n\n".join(text_blocks[:2]) if text_blocks else "No content extracted."
    except Exception as e:
        return f"Failed to fetch: {str(e)}"



        

# @router.post("/chat")
# async def chat(
#     input: Optional[ChatInput] = None,
#     message: Optional[str] = Form(None),
#     email: Optional[str] = Form(None),
#     files: Optional[List[UploadFile]] = File(None)
# ):
#     try:
#         # Handle both JSON input (existing) and Form input (with files)
#         if input:
#             user_email = input.email
#             user_message = input.message.strip()
#             chat_collection.insert_one(input.dict())
#         else:
#             user_email = email
#             user_message = message.strip() if message else ""
            
#             # Store chat message
#             chat_data = {
#                 "email": user_email,
#                 "message": user_message,
#                 "sender": "user",
#                 "timestamp": datetime.utcnow()
#             }
#             chat_collection.insert_one(chat_data)

#         logger.info(f"Chat request from {user_email}: {user_message}")
#         state = user_states[user_email]

#         # Handle file uploads first
#         uploaded_files_info = []
#         if files:
#             for file in files:
#                 if file.filename:  # Check if file was actually uploaded
#                     file_info = await save_uploaded_file(file, user_email)
#                     uploaded_files_info.append(file_info)
#                     # Add to user state
#                     state["uploaded_files"].append(file_info)

#         # Handle restart command
#         if user_message.lower() == "restart":
#             user_states[user_email] = {
#                 "preapproval_started": True,
#                 "current_question_index": 0,
#                 "answers": {},
#                 "uploaded_files": []
#             }
#             logger.info("Pre-approval restarted")
#             return {"reply": "Pre-approval process restarted.\n\n" + PREAPPROVAL_FIELDS[0]["question"]}

#         # Handle back command
#         if user_message.lower() == "back" and state["preapproval_started"]:
#             state["current_question_index"] = max(state["current_question_index"] - 1, 0)
#             logger.info("Navigated back to previous question")
#             return {"reply": f"Okay, let's go back.\n{PREAPPROVAL_FIELDS[state['current_question_index']]['question']}"}

#         # Start pre-approval process
#         if any(keyword in user_message.lower() for keyword in ["preapproval", "pre-approval", "pre approval"]) and not state["preapproval_started"]:
#             state["preapproval_started"] = True
#             state["current_question_index"] = 0
#             # Auto-fill email immediately when starting pre-approval
#             state["answers"]["email"] = user_email
#             return {"reply": f"Great! Let's begin your pre-approval process.\n\n{PREAPPROVAL_FIELDS[0]['question']}"}

#         # Handle pre-approval process
#         if state["preapproval_started"]:
       
#             idx = state["current_question_index"]
#             if idx >= len(PREAPPROVAL_FIELDS):
#                 return {"reply": "Pre-approval process already completed!"}
                
#             field = PREAPPROVAL_FIELDS[idx]
#             key = field["key"]

#               # Auto-fill for email field
#             if key == "email" and not state["answers"].get("email"):
#                 reply = f"Your email is: {user_email}\nDo you want to keep this email? (yes/no)"
#                 if user_message.lower() in ["yes", "y", ""]:
#                     state["answers"]["email"] = user_email
#                     message_histories[user_email].append({
#                         "role": "user",
#                         "content": f"[Pre-Approval Answer] email: {user_email}"
#                     })
#                     state["current_question_index"] += 1
#                     next_q = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
#                     return {"reply": f"✅ Email kept as {user_email}.\n\n{next_q}"}
#                 elif user_message.lower() in ["no", "n"]:
#                     return {"reply": "Please enter your preferred email:"}
#                 elif "@" in user_message:
#                     state["answers"]["email"] = user_message
#                     message_histories[user_email].append({
#                         "role": "user",
#                         "content": f"[Pre-Approval Answer] email: {user_message}"
#                     })
#                     state["current_question_index"] += 1
#                     next_q = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
#                     return {"reply": f"✅ Email updated to {user_message}.\n\n{next_q}"}
#                 else:
#                     return {"reply": reply}


#             # Special handling for bank_statements (file upload required)
#             if key == "bank_statements":
#                 if not uploaded_files_info and not user_message.strip():
#                     return {"reply": "❌ Error: Please upload your bank statements (PDF, JPG, or PNG files) to continue with the pre-approval process.\n\nYou can upload multiple files if needed."}
                
#                 if uploaded_files_info:
#                     file_names = [f["original_filename"] for f in uploaded_files_info]
#                     state["answers"][key] = f"Files uploaded: {', '.join(file_names)}"
                    
#                     message_histories[user_email].append({
#                         "role": "user",
#                         "content": f"[Pre-Approval Answer] {key}: {', '.join(file_names)}"
#                     })
#                     # Move to next question or complete process
#                     state["current_question_index"] += 1
                    
#                     if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
#                         next_question = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
#                         return {"reply": f"✅ Thank you! I've received your bank statements: {', '.join(file_names)}\n\n{next_question}"}
#                     else:
#                         # Complete pre-approval process
#                         pre_approvals_collection.insert_one({
#                             "email": user_email,
#                             "data": state["answers"],
#                             "uploaded_files": state["uploaded_files"],
#                             "submitted_at": datetime.utcnow()
#                         })

#                         # Generate PDF
#                         # pdf_path = generate_preapproval_pdf(state["answers"], user_email)
#                         #spread sheet
#                         spreadsheet_url = write_preapproval_to_sheet(state["answers"])
#                         # Send PDF via email
#                         send_email_with_attachment(
#                             to_email=user_email,
#                             subject="Your Pre-Approval Application",
#                             body=EMAIL_BODY,
#                             # file_path=pdf_path,
#                         )
#                         send_client_notification_with_attachments(
#                             client_email="devivijay.thalatam@gmail.com",  # Replace with actual client email
#                             customer_email=user_email,
#                             preapproval_data=state["answers"],
#                             uploaded_files=state["uploaded_files"],
#                         )


#                         del user_states[user_email]
#                         return {"reply": f"I've received your bank statements: {', '.join(file_names)}\n\n✅ Thanks! We've received your complete pre-approval application with all required documents."}
#                 else:
#                     return {"reply": "❌ Error: Bank statements are required to complete your pre-approval. Please upload your recent bank statements (PDF, JPG, or PNG files)."}

#             # Handle other pre-approval questions
#             else:
#                 # Validate input if validation function exists
#                 if "validate" in field and not field["validate"](user_message):
#                     logger.warning(f"Validation failed for {key}: {user_message}")
#                     return {"reply": f"Invalid input. Please try again.\n\n{field['question']}"}

#                 state["answers"][key] = user_message
#                 state["current_question_index"] += 1

#                 if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
#                     next_field = PREAPPROVAL_FIELDS[state["current_question_index"]]
#                     next_question = next_field["question"]
                    
#                     # Add special instruction for bank statements
#                     if next_field["key"] == "bank_statements":
#                         next_question += "\n\n📎 Important: You must upload your bank statement files to proceed. Text responses will not be accepted for this step."
                    
#                     logger.info(f"Next question: {next_question}")
#                     return {"reply": next_question}

#         # Handle regular chat (non-pre-approval)
#         if not message_histories[user_email]:
#             message_histories[user_email].append({"role": "system", "content": SYSTEM_PROMPT})

#         message_histories[user_email].append({"role": "user", "content": user_message})

#         # Handle file upload acknowledgment in regular chat
#         if uploaded_files_info:
#             file_names = [f["original_filename"] for f in uploaded_files_info]
#             file_acknowledgment = f"✅ I've received your file(s): {', '.join(file_names)}. "
            
#             # Add context about the files to the conversation
#             file_context = f"User uploaded files: {', '.join(file_names)}. "
#             message_histories[user_email].append({"role": "system", "content": file_context})

#         # Real-time mortgage rate or government resource handling
#         user_lower = user_message.lower()
#         if any(kw in user_lower for kw in ["mortgage rates", "home loan rates", "current rates", "rates"]):
#             try:
#                 rates = get_mortgage_rates()
#                 formatted_rates = "\n".join([f"{k}: {v}" for k, v in rates.items()])
#                 bot_reply = (
#                     f"To day current mortgage rates:\n{formatted_rates}\n\n"
#                     "Please reach out to us to get a personalized quote. "
#                     "Let me know if you would like to connect with a Loan Officer."
#                 )
#             except Exception:
#                 bot_reply = "Sorry, I couldn't fetch the latest mortgage rates right now."
#         elif any(kw in user_lower for kw in ["fannie mae", "freddie mac", "hud", "government loan"]):
#             summaries = {
#                 "Fannie Mae": get_fannie_mae_summary(),
#                 "Freddie Mac": get_freddie_mac_summary(),
#                 "HUD FHA": get_hud_fha_summary()
#             }
#             bot_reply = "Here is official information on U.S. housing finance programs:\n\n"
#             for name, summary in summaries.items():
#                 bot_reply += f"**{name}**\n{summary}\n\n"
#         else:
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=message_histories[user_email],
#                 temperature=0.7,
#                 max_tokens=300
#             )
#             bot_reply = response.choices[0].message.content.strip()

#         # Add file acknowledgment to regular responses
#         if uploaded_files_info and not state["preapproval_started"]:
#             file_names = [f["original_filename"] for f in uploaded_files_info]
#             bot_reply = f"✅ I've received your file(s): {', '.join(file_names)}. " + bot_reply

#         # Apply text replacements
#         replacements = {
#             "speak with a lender": "please reach out to us",
#             "talk to a lender": "please reach out to us",
#             "consult with a lender": "please reach out to us",
#             "contact a lender": "please reach out to us",
#             "talk to your bank": "please reach out to us",
#             "consult your bank": "please reach out to us",
#             "speak to your bank": "please reach out to us",
#             "consult with your lender": "please reach out to us",
#             "reach out to a lender": "please reach out to us",
#         }

#         for phrase, replacement in replacements.items():
#             bot_reply = bot_reply.replace(phrase, replacement)

#         message_histories[user_email].append({"role": "assistant", "content": bot_reply})

#         chat_collection.insert_one({
#             "email": user_email,
#             "message": bot_reply,
#             "sender": "bot",
#             "timestamp": datetime.utcnow()
#         })

#         return {"reply": bot_reply}

#     except asyncio.CancelledError:
#         raise HTTPException(status_code=499, detail="Request cancelled by client")
#     except Exception as e:
#         logger.error(f"Unexpected error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))



@router.post("/chat")
async def chat(
    input: Optional[ChatInput] = None,
    message: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    try:
        # Handle both JSON input (existing) and Form input (with files)
        if input:
            user_email = input.email
            user_message = input.message.strip()
            chat_collection.insert_one(input.dict())
        else:
            user_email = email
            user_message = message.strip() if message else ""
            
            # Store chat message
            chat_data = {
                "email": user_email,
                "message": user_message,
                "sender": "user",
                "timestamp": datetime.utcnow()
            }
            chat_collection.insert_one(chat_data)

        logger.info(f"Chat request from {user_email}: {user_message}")
        state = user_states[user_email]

        # Handle file uploads first
        uploaded_files_info = []
        if files:
            for file in files:
                if file.filename:  # Check if file was actually uploaded
                    file_info = await save_uploaded_file(file, user_email)
                    uploaded_files_info.append(file_info)
                    # Add to user state
                    state["uploaded_files"].append(file_info)

        # Handle restart command
        if user_message.lower() == "restart":
            user_states[user_email] = {
                "preapproval_started": True,
                "current_question_index": 0,
                "answers": {},
                "uploaded_files": []
            }
            logger.info("Pre-approval restarted")
            return {"reply": "Pre-approval process restarted.\n\n" + PREAPPROVAL_FIELDS[0]["question"]}

        # Handle back command
        if user_message.lower() == "back" and state["preapproval_started"]:
            state["current_question_index"] = max(state["current_question_index"] - 1, 0)
            logger.info("Navigated back to previous question")
            return {"reply": f"Okay, let's go back.\n{PREAPPROVAL_FIELDS[state['current_question_index']]['question']}"}

        # Start pre-approval process
        if any(keyword in user_message.lower() for keyword in ["preapproval", "pre-approval", "pre approval"]) and not state["preapproval_started"]:
            state["preapproval_started"] = True
            state["current_question_index"] = 0
            # Auto-fill email immediately when starting pre-approval
            state["answers"]["email"] = user_email
            
            # Check if first question is email field
            if PREAPPROVAL_FIELDS[0]["key"] == "email":
                # Show email confirmation message
                return {"reply": f"Great! Let's begin your pre-approval process.\n\n• Your email is: {user_email}\n• Do you want to keep this email? (yes/no)"}
            else:
                return {"reply": f"Great! Let's begin your pre-approval process.\n\n{PREAPPROVAL_FIELDS[0]['question']}"}

        # Handle pre-approval process
        if state["preapproval_started"]:
            idx = state["current_question_index"]
            if idx >= len(PREAPPROVAL_FIELDS):
                return {"reply": "Pre-approval process already completed!"}
                
            field = PREAPPROVAL_FIELDS[idx]
            key = field["key"]

            # Auto-fill for email field
            if key == "email":
                # If email is not set in answers yet, show the confirmation
                if not state["answers"].get("email"):
                    state["answers"]["email"] = user_email
                    return {"reply": f"• Your email is: {user_email}\n• Do you want to keep this email? (yes/no)"}
                
                # Handle user response to email confirmation
                if user_message.lower() in ["yes", "y"]:
                    # Keep the pre-filled email
                    message_histories[user_email].append({
                        "role": "user",
                        "content": f"[Pre-Approval Answer] email: {user_email}"
                    })
                    state["current_question_index"] += 1
                    
                    if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                        next_q = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
                        return {"reply": f"✅ Email kept as {user_email}.\n\n{next_q}"}
                    else:
                        # This shouldn't happen if email is first question, but handle it
                        return {"reply": f"✅ Email kept as {user_email}."}
                        
                elif user_message.lower() in ["no", "n"]:
                    return {"reply": "Please enter your preferred email:"}
                    
                elif "@" in user_message:
                    # User provided a different email
                    state["answers"]["email"] = user_message
                    message_histories[user_email].append({
                        "role": "user",
                        "content": f"[Pre-Approval Answer] email: {user_message}"
                    })
                    state["current_question_index"] += 1
                    
                    if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                        next_q = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
                        return {"reply": f"✅ Email updated to {user_message}.\n\n{next_q}"}
                    else:
                        return {"reply": f"✅ Email updated to {user_message}."}
                else:
                    # Invalid response, ask again
                    return {"reply": f"• Your email is: {user_email}\n• Do you want to keep this email? (yes/no)"}

            # Special handling for bank_statements (file upload required)
            elif key == "bank_statements":
                if not uploaded_files_info and not user_message.strip():
                    return {"reply": "❌ Error: Please upload your bank statements (PDF, JPG, or PNG files) to continue with the pre-approval process.\n\nYou can upload multiple files if needed."}
                
                if uploaded_files_info:
                    file_names = [f["original_filename"] for f in uploaded_files_info]
                    state["answers"][key] = f"Files uploaded: {', '.join(file_names)}"
                    
                    message_histories[user_email].append({
                        "role": "user",
                        "content": f"[Pre-Approval Answer] {key}: {', '.join(file_names)}"
                    })
                    # Move to next question or complete process
                    state["current_question_index"] += 1
                    
                    if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                        next_question = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
                        return {"reply": f"✅ Thank you! I've received your bank statements: {', '.join(file_names)}\n\n{next_question}"}
                    else:
                        # Complete pre-approval process
                        pre_approvals_collection.insert_one({
                            "email": user_email,
                            "data": state["answers"],
                            "uploaded_files": state["uploaded_files"],
                            "submitted_at": datetime.utcnow()
                        })

                        # Generate PDF
                        # pdf_path = generate_preapproval_pdf(state["answers"], user_email)
                        #spread sheet
                        spreadsheet_url = write_preapproval_to_sheet(state["answers"])
                        # Send PDF via email
                        send_email_with_attachment(
                            to_email=user_email,
                            subject="Your Pre-Approval Application",
                            body=EMAIL_BODY,
                            # file_path=pdf_path,
                        )
                        send_client_notification_with_attachments(
                            client_email= CLIENT_EMAIL, 
                            customer_email=user_email,
                            preapproval_data=state["answers"],
                            uploaded_files=state["uploaded_files"],
                        )

                        del user_states[user_email]
                        return {"reply": f"I've received your bank statements: {', '.join(file_names)}\n\n✅ Thanks! We've received your complete pre-approval application with all required documents."}
                else:
                    return {"reply": "❌ Error: Bank statements are required to complete your pre-approval. Please upload your recent bank statements (PDF, JPG, or PNG files)."}

            # Handle other pre-approval questions
            else:
                # Validate input if validation function exists
                if "validate" in field and not field["validate"](user_message):
                    logger.warning(f"Validation failed for {key}: {user_message}")
                    return {"reply": f"Invalid input. Please try again.\n\n{field['question']}"}

                state["answers"][key] = user_message
                state["current_question_index"] += 1

                if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                    next_field = PREAPPROVAL_FIELDS[state["current_question_index"]]
                    next_question = next_field["question"]
                    
                    # Add special instruction for bank statements
                    if next_field["key"] == "bank_statements":
                        next_question += "\n\n📎 Important: You must upload your bank statement files to proceed. Text responses will not be accepted for this step."
                    
                    logger.info(f"Next question: {next_question}")
                    return {"reply": next_question}

        # Handle regular chat (non-pre-approval)
        if not message_histories[user_email]:
            message_histories[user_email].append({"role": "system", "content": SYSTEM_PROMPT})

        message_histories[user_email].append({"role": "user", "content": user_message})

        # Handle file upload acknowledgment in regular chat
        if uploaded_files_info:
            file_names = [f["original_filename"] for f in uploaded_files_info]
            file_acknowledgment = f"✅ I've received your file(s): {', '.join(file_names)}. "
            
            # Add context about the files to the conversation
            file_context = f"User uploaded files: {', '.join(file_names)}. "
            message_histories[user_email].append({"role": "system", "content": file_context})

        # Real-time mortgage rate or government resource handling
        user_lower = user_message.lower()
        if any(kw in user_lower for kw in ["mortgage rates", "home loan rates", "current rates", "rates"]):
            try:
                rates = get_mortgage_rates()
                formatted_rates = "\n".join([f"{k}: {v}" for k, v in rates.items()])
                bot_reply = (
                    f"To day current mortgage rates:\n{formatted_rates}\n\n"
                    "Please reach out to us to get a personalized quote. "
                    "Let me know if you would like to connect with a Loan Officer."
                )
            except Exception:
                bot_reply = "Sorry, I couldn't fetch the latest mortgage rates right now."
        elif any(kw in user_lower for kw in ["fannie mae", "freddie mac", "hud", "government loan"]):
            summaries = {
                "Fannie Mae": get_fannie_mae_summary(),
                "Freddie Mac": get_freddie_mac_summary(),
                "HUD FHA": get_hud_fha_summary()
            }
            bot_reply = "Here is official information on U.S. housing finance programs:\n\n"
            for name, summary in summaries.items():
                bot_reply += f"**{name}**\n{summary}\n\n"
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message_histories[user_email],
                temperature=0.7,
                max_tokens=300
            )
            bot_reply = response.choices[0].message.content.strip()

        # Add file acknowledgment to regular responses
        if uploaded_files_info and not state["preapproval_started"]:
            file_names = [f["original_filename"] for f in uploaded_files_info]
            bot_reply = f"✅ I've received your file(s): {', '.join(file_names)}. " + bot_reply

        # Apply text replacements
        replacements = {
            "speak with a lender": "please reach out to us",
            "talk to a lender": "please reach out to us",
            "consult with a lender": "please reach out to us",
            "contact a lender": "please reach out to us",
            "talk to your bank": "please reach out to us",
            "consult your bank": "please reach out to us",
            "speak to your bank": "please reach out to us",
            "consult with your lender": "please reach out to us",
            "reach out to a lender": "please reach out to us",
        }

        for phrase, replacement in replacements.items():
            bot_reply = bot_reply.replace(phrase, replacement)

        message_histories[user_email].append({"role": "assistant", "content": bot_reply})

        chat_collection.insert_one({
            "email": user_email,
            "message": bot_reply,
            "sender": "bot",
            "timestamp": datetime.utcnow()
        })

        return {"reply": bot_reply}

    except asyncio.CancelledError:
        raise HTTPException(status_code=499, detail="Request cancelled by client")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))