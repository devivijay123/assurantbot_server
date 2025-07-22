from fastapi import APIRouter, FastAPI, Form
from pydantic import BaseModel
from fastapi.responses import FileResponse, StreamingResponse
import uuid
import os
from fpdf import FPDF

from app.models import MortgageRequest, PreApprovalRequest

router = APIRouter()

@router.get("/")
def test_mortgage_api():
    return {"message": "Mortgage Calculator API is up and running!"}

@router.post("/calculate")
def calculate_mortgage(data: MortgageRequest):
    P = data.loanAmount
    r = data.interestRate / 100 / 12
    n = data.loanTerm * 12

    if r == 0:
        monthly_payment = P / n
    else:
        monthly_payment = P * r * (1 + r) ** n / ((1 + r) ** n - 1)

    return {"monthlyPayment": round(monthly_payment, 2)}

@router.post("/generate-letter/")
def generate_letter(
    name: str = Form(...),
    email: str = Form(...),
    amount: str = Form(...)
):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Pre-Approval Letter", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"This is to confirm that {name} with email {email} is pre-approved for a mortgage amount of ${amount}.")

    # Save the PDF
    filename = f"preapproval_{uuid.uuid4().hex}.pdf"
    filepath = f"./pdfs/{filename}"
    os.makedirs("pdfs", exist_ok=True)
    pdf.output(filepath)

    return {"message": "Submitted Successfully", "pdf_url": f"http://localhost:8000/download/{filename}"}

@router.get("/download/{filename}")
def download_pdf(filename: str):
    return FileResponse(path=f"./pdfs/{filename}", media_type='application/pdf', filename=filename)
