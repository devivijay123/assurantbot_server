from fpdf import FPDF
from datetime import datetime

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
