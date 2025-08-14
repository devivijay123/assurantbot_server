import asyncio
from collections import defaultdict
from fastapi import APIRouter, HTTPException, logger, Form, UploadFile, File
from fastapi.logger import logger
from openai import AzureOpenAI, BaseModel, OpenAI
import os
from dotenv import load_dotenv
from typing import Optional,  List
from app.constants import PREAPPROVAL_FIELDS, SYSTEM_PROMPT, EMAIL_BODY
from app.database import chat_collection, pre_approvals_collection
from datetime import datetime
import uuid
from pathlib import Path
import aiofiles 
from app.email_service import send_client_notification_with_attachments, send_email_with_attachment, send_email_with_multiple_attachments
from app.pdf_generator import write_preapproval_to_sheet 
load_dotenv() 
message_histories = defaultdict(list)


router = APIRouter(prefix="/user-chat", tags=["Chat"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
#state management
user_states = defaultdict(lambda: {
    "preapproval_started": False,
    "current_question_index": -1,
    "answers": {},
    "uploaded_files": []
})
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class ChatInput(BaseModel):
    email: str
    message: str
    sender: str = "user"

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
        # file_path = UPLOAD_DIR / unique_filename
        file_path = unique_filename
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

@router.get("/")
async def root():
    return {"message": "chat routes API"}


@router.get("/mortgage-rates")
async def get_live_mortgage_rates():
    """
    Returns live daily mortgage rates using GPT-5 (no scraping needed).
    """
    try:
        # Ask GPT-5 directly for live rates
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a mortgage rate assistant that provides accurate, up-to-date rates."},
                {"role": "user", "content": "Give me today's average US mortgage rates for 30-year fixed, 15-year fixed, and 5/1 ARM in percentage format."}
            ],
            max_completion_tokens=300
        )

        bot_reply = response.choices[0].message.content.strip()

        return {
            "reply": bot_reply
        }

    except Exception as e:
        logger.error(f"Error fetching live mortgage rates: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch live mortgage rates at this moment.")
@router.post("/pre-approval")
async def pre_approval_form(
    email: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    try:
        print("email",email)
        print("message", message)
        if not email:
            raise HTTPException(status_code=400, detail="Email is required.")

        if email not in user_states:
            user_states[email] = {
                "preapproval_started": False,
                "current_question_index": 0,
                "answers": {},
                "uploaded_files": []
            }

        state = user_states[email]
        uploaded_files_info = []

        # Handle uploaded files
        if files:
            for file in files:
                if file.filename:
                    file_info = await save_uploaded_file(file, email)
                    uploaded_files_info.append(file_info)
                    state["uploaded_files"].append(file_info)

        # Restart command
        if message and message.lower() == "restart":
            user_states[email] = {
                "preapproval_started": True,
                "current_question_index": 0,
                "answers": {},
                "uploaded_files": []
            }
            return {"reply": "Pre-approval restarted.\n\n" + PREAPPROVAL_FIELDS[0]["question"]}

        # Back command
        if message and message.lower() == "back" and state["preapproval_started"]:
            state["current_question_index"] = max(state["current_question_index"] - 1, 0)
            return {"reply": f"Okay, let's go back.\n{PREAPPROVAL_FIELDS[state['current_question_index']]['question']}"}

        # Start process
        if message and any(k in message.lower() for k in ["preapproval", "pre-approval", "pre approval", "pre app", "pre-app", "preapp"]) and not state["preapproval_started"]:
            state["preapproval_started"] = True
            state["current_question_index"] = 0
            state["answers"]["email"] = email

            if PREAPPROVAL_FIELDS[0]["key"] == "email":
                return {"reply": f"Great! Let's begin your pre-approval process.\n\n• Your email is: {email}\n• Do you want to keep this email? (yes/no)"}
            else:
                return {"reply": f"Great! Let's begin your pre-approval process.\n\n{PREAPPROVAL_FIELDS[0]['question']}"}

        # Handle Q&A
        if state["preapproval_started"]:
            idx = state["current_question_index"]
            if idx >= len(PREAPPROVAL_FIELDS):
                return {"reply": "Pre-approval process already completed!"}

            field = PREAPPROVAL_FIELDS[idx]
            key = field["key"]

            # Special case: email
            if key == "email":
                # If email is not set in answers yet, show the confirmation
                if not state["answers"].get("email"):
                    state["answers"]["email"] = email
                    return {"reply": f"• Your email is: {email}\n• Do you want to keep this email? (yes/no)"}
                
                # Handle user response to email confirmation
                if message.lower() in ["yes", "y"]:
                    # Keep the pre-filled email
                    message_histories[email].append({
                        "role": "user",
                        "content": f"[Pre-Approval Answer] email: {email}"
                    })
                    state["current_question_index"] += 1
                    
                    if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                        next_q = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
                        return {"reply": f"✅ Email kept as {email}.\n\n{next_q}"}
                    else:
                        # This shouldn't happen if email is first question, but handle it
                        return {"reply": f"✅ Email kept as {email}."}
                        
                elif message.lower() in ["no", "n"]:
                    return {"reply": "Please enter your preferred email:"}
                    
                elif "@" in message:
                    # User provided a different email
                    state["answers"]["email"] = message
                    message_histories[email].append({
                        "role": "user",
                        "content": f"[Pre-Approval Answer] email: {message}"
                    })
                    state["current_question_index"] += 1
                    
                    if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                        next_q = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
                        return {"reply": f"✅ Email updated to {message}.\n\n{next_q}"}
                    else:
                        return {"reply": f"✅ Email updated to {message}."}
                else:
                    # Invalid response, ask again
                    return {"reply": f"• Your email is: {email}\n• Do you want to keep this email? (yes/no)"}
            # Special case: bank statements
            elif key == "bank_statements":
                if not uploaded_files_info and not (message and message.strip()):
                    return {"reply": "❌ Please upload your bank statements to continue."}

                if uploaded_files_info:
                    file_names = [f["original_filename"] for f in uploaded_files_info]
                    state["answers"][key] = f"Files uploaded: {', '.join(file_names)}"
                    state["current_question_index"] += 1

                    if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                        next_question = PREAPPROVAL_FIELDS[state["current_question_index"]]["question"]
                        return {"reply": f"✅ Received bank statements: {', '.join(file_names)}\n\n{PREAPPROVAL_FIELDS[state['current_question_index']]['question']}"}
                    else:
                        pre_approvals_collection.insert_one({
                            "email": email,
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
                            to_email=email,
                            subject="Your Pre-Approval Application",
                            body=EMAIL_BODY,
                            # file_path=pdf_path,
                        )
                        send_client_notification_with_attachments(
                            client_email= CLIENT_EMAIL, 
                            customer_email=email,
                            preapproval_data=state["answers"],
                            uploaded_files=state["uploaded_files"],
                        )
                        del user_states[email]
                        return {"reply": f"✅ Thanks! We've received your complete pre-approval application."}
                else:
                    return {"reply": "❌ Error: Bank statements are required to complete your pre-approval."}

            # All other fields
            else:
                if "validate" in field and not field["validate"](message):
                    return {"reply": f"Invalid input. Please try again.\n\n{field['question']}"}

                state["answers"][key] = message
                state["current_question_index"] += 1

                if state["current_question_index"] < len(PREAPPROVAL_FIELDS):
                    next_field = PREAPPROVAL_FIELDS[state["current_question_index"]]
                    next_question = next_field["question"]

                    if next_field["key"] == "bank_statements":
                        next_question += "\n\n📎 Please upload your bank statements."
                    return {"reply": next_question}

    except asyncio.CancelledError:
        raise HTTPException(status_code=499, detail="Request cancelled by client")
    except Exception as e:
        logger.error(f"Unexpected error in pre-approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/chatbot")
async def chatbot(
    input: Optional[ChatInput] = None,
    message: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    try:
        print("DEBUG email:", email)
        print("DEBUG message:", message)
        print("DEBUG files:", files)
        # Initialize user history if not present
        if email not in message_histories or not message_histories[email]:
            message_histories[email] = [
                {"role": "system", "content":  """
You are a knowledgeable and friendly assistant specializing in U.S. home loans and mortgages. 
You provide clear, accurate, and up-to-date information about:
- Home loan types (fixed-rate, adjustable-rate, FHA, VA, USDA, jumbo, etc.)
- Mortgage interest rates and factors affecting them
- Loan eligibility, credit scores, and down payment requirements
- The home buying process, including pre-approval, application, underwriting, and closing
- Refinancing options and strategies
- Federal and state-specific programs for first-time buyers

Guidelines:
1. Only answer questions related to U.S. home loans, mortgages, or closely related financial topics.
2. If the question is outside your scope, politely say:
   "I specialize in U.S. home loans. Could you ask something related to that?"
3. Use plain, easy-to-understand language.
4. Provide examples, numbers, and explanations when helpful.
5. Keep tone professional but approachable, like a trusted loan advisor.
"""}
            ]
        print("DEBUG history before GPT call:", message_histories.get(email))
        # Store user message
        user_message = message.strip() if message else ""
        if user_message:
            message_histories[email].append({"role": "user", "content": user_message})
            chat_collection.insert_one({
                "email": email,
                "message": user_message,
                "sender": "user",
                "timestamp": datetime.utcnow()
            })

        # Handle file uploads
        uploaded_files_info = []
        if files:
            for file in files:
                if file.filename:
                    file_info = await save_uploaded_file(file, email)
                    uploaded_files_info.append(file_info)
                    # Add file context for the model
                    file_context = f"User uploaded file: {file_info['original_filename']}"
                    message_histories[email].append({"role": "system", "content": file_context})

        # Send to GPT-5
        response = client.chat.completions.create(
            model="gpt-5",
            messages=message_histories[email],
            max_completion_tokens=1500
        )
        print("DEBUG GPT raw response:", response)
        print("DEBUG 12345678 reply content:", response.choices[0].message.content)
        bot_reply = response.choices[0].message.content.strip()

        # Store bot reply
        message_histories[email].append({"role": "assistant", "content": bot_reply})
        chat_collection.insert_one({
            "email": email,
            "message": bot_reply,
            "sender": "bot",
            "timestamp": datetime.utcnow()
        })

        # Add file acknowledgment if any files uploaded
        if uploaded_files_info:
            file_names = ", ".join(f["original_filename"] for f in uploaded_files_info)
            bot_reply += f"\n\n✅ I've received your file(s): {file_names}."

        return {"reply": bot_reply}

    except asyncio.CancelledError:
        raise HTTPException(status_code=499, detail="Request cancelled by client")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
