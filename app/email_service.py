
from datetime import datetime
import smtplib
import os
from email.message import EmailMessage
from bson import ObjectId
from dotenv import load_dotenv
import gridfs
from app.database import db

fs = gridfs.GridFS(db)

load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email_with_attachment(to_email, subject, body, file_path):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg.set_content(body)

        with open(file_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)

        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        raise Exception(f"Failed to send email: {e}")


# Add this helper function for sending client notifications with attachments
def send_client_notification_with_attachments(client_email, customer_email, preapproval_data, uploaded_files):
    try:
        # Prepare email body
        body = f"""
New Pre-Approval Application Received

Customer Email: {customer_email}
Submission Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Pre-Approval Details:
"""
        for key, value in preapproval_data.items():
            body += f"{key.replace('_', ' ').title()}: {value}\n"

        body += f"\nUploaded Files: {len(uploaded_files)} file(s)\n"

        # ✅ Prepare actual file paths (or download from GridFS)
        file_paths = []
        for f in uploaded_files:
            if "file_path" in f and os.path.exists(f["file_path"]):
                # ✅ File exists locally
                file_paths.append(f["file_path"])
            elif "file_id" in f:  
                # ✅ Download from GridFS
                temp_path = f"/tmp/{f.get('original_filename', 'file')}"
                with open(temp_path, "wb") as temp_file:
                    grid_out = fs.get(ObjectId(f["file_id"]))  # fs = GridFS instance
                    temp_file.write(grid_out.read())
                file_paths.append(temp_path)

        # ✅ Send email with attachments (PDF/JPG/PNG supported)
        send_email_with_multiple_attachments(
            to_email=client_email,
            subject=f"New Pre-Approval Application - {customer_email}",
            body=body,
            file_paths=file_paths
        )

        print(f"✅ Email sent to {client_email} with {len(file_paths)} attachments.")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise Exception(f"Failed to send client notification: {str(e)}")
        print(f"DEBUG: ERROR in send_client_notification_with_attachments: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to send client notification: {str(e)}")


def send_email_with_multiple_attachments(to_email, subject, body, file_paths):
    """Send email with multiple attachments using your existing email setup"""
    print("=== DEBUG: send_email_with_multiple_attachments called ===")
    print(f"DEBUG: to_email = {to_email}")
    print(f"DEBUG: subject = {subject}")
    print(f"DEBUG: body length = {len(body)}")
    print(f"DEBUG: file_paths = {file_paths}")
    
    try:
        from email.message import EmailMessage
        import smtplib
        import os
        
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS  # Using your existing EMAIL_ADDRESS
        msg["To"] = to_email
        msg.set_content(body)
        
        print(f"DEBUG: Email message created with sender: {EMAIL_ADDRESS}")
        
        # Add multiple attachments
        for i, file_path in enumerate(file_paths):
            if os.path.exists(file_path):
                print(f"DEBUG: Processing attachment {i+1}: {file_path}")
                
                with open(file_path, "rb") as f:
                    file_data = f.read()
                    file_name = os.path.basename(file_path)
                    
                    print(f"DEBUG: File {file_name} loaded, size: {len(file_data)} bytes")
                    
                    # Determine file type for proper attachment
                    if file_name.lower().endswith('.pdf'):
                        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)
                        print(f"DEBUG: Added PDF attachment: {file_name}")
                    elif file_name.lower().endswith(('.jpg', '.jpeg')):
                        msg.add_attachment(file_data, maintype="image", subtype="jpeg", filename=file_name)
                        print(f"DEBUG: Added JPEG attachment: {file_name}")
                    elif file_name.lower().endswith('.png'):
                        msg.add_attachment(file_data, maintype="image", subtype="png", filename=file_name)
                        print(f"DEBUG: Added PNG attachment: {file_name}")
                    elif file_name.lower().endswith(('.doc', '.docx')):
                        msg.add_attachment(file_data, maintype="application", subtype="vnd.openxmlformats-officedocument.wordprocessingml.document", filename=file_name)
                        print(f"DEBUG: Added Word document attachment: {file_name}")
                    else:
                        # Generic attachment for other file types
                        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)
                        print(f"DEBUG: Added generic attachment: {file_name}")
                        
            else:
                print(f"DEBUG: WARNING - File does not exist: {file_path}")
        
        print("DEBUG: All attachments processed, sending email...")
        
        # Send email using your existing SMTP settings
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Using your existing EMAIL_PASSWORD
            smtp.send_message(msg)
            
        print(f"DEBUG: Email sent successfully to {to_email} with {len(file_paths)} attachments")
        
    except Exception as e:
        print(f"DEBUG: Email sending failed: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Email traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to send email with multiple attachments: {str(e)}")


def send_email_with_attachment(to_email, subject, body):
    """Your existing single attachment function"""
    try:
        from email.message import EmailMessage
        import smtplib
        import os
        
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg.set_content(body)

        # with open(file_path, "rb") as f:
        #     file_data = f.read()
        #     file_name = os.path.basename(file_path)

        # msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        raise Exception(f"Failed to send email: {e}")


