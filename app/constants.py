import re

PREAPPROVAL_FIELDS = [
     {
        "key": "email",
        "question": "Email Address",
        "validate": lambda v: bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v.strip()))
    },
    {
        "key": "borrower_name",
        "question": "Please enter Borrower First Name and Last Name.",
        "validate": lambda v: bool(re.match(r"^[A-Za-z ]{2,}$", v.strip()))
    },
    {
        "key": "co_borrower_name",
        "question": "Co-Borrower First Name & Last Name (If applicable).",
        "validate": lambda v: v.strip() == "" or bool(re.match(r"^[A-Za-z ]{2,}$", v.strip()))
    },
   
    {
        "key": "phone",
        "question": "Phone Number",
        "validate": lambda v: bool(re.match(r"^\d{10,15}$", v.strip()))
    },
    {
        "key": "purchase_price",
        "question": "Purchase Price",
        "validate": lambda v: v.replace(",", "").replace(".", "").isdigit() and float(v.replace(",", "")) > 0
    },
    {
        "key": "loan_amount",
        "question": "Loan Amount",
        "validate": lambda v: v.replace(",", "").replace(".", "").isdigit() and float(v.replace(",", "")) > 0
    },
    {
        "key": "down_payment",
        "question": "Down Payment (The source for these funds should be readily accessible such as cash, stock, 401K, CDs, etc.)",
        "validate": lambda v: v.replace(",", "").replace(".", "").isdigit() and float(v.replace(",", "")) >= 0
    },
    {
        "key": "property_address",
        "question": "Property Address (put TBD if unknown)",
        "validate": lambda v: len(v.strip()) >= 2
    },
    {
        "key": "gross_pay",
        "question": "Average Annual Documented Gross Pay over the last 2 years",
        "validate": lambda v: v.replace(",", "").replace(".", "").isdigit() and float(v.replace(",", "")) > 0
    },
    {
        "key": "foreign_assets",
        "question": "Do you declare foreign assets and investments in your tax returns? (Yes/No)",
        "validate": lambda v: v.strip().lower() in ["yes", "no"]
    },
    {
        "key": "credit_score",
        "question": "What is the average credit score reflected across all your banks and credit cards (Don’t use Credit Karma)?",
        "validate": lambda v: v.isdigit()
    },
    {
        "key": "bank_statements",
        "question": "Please upload your recent bank statements (PDF/Images).",
        "type": "file",
        "allowed_formats": ["pdf", "jpg", "png"]
    }
]


SYSTEM_PROMPT = (
    "You are a U.S. based loan officer that answers only questions related to loans, mortgages, and housing finance. "
    "You provide accurate, practical information specifically for users in the United States.\n\n"
    "Always format detailed responses in lists or tables where applicable.\n\n"
    "You are allowed to fetch and present the latest available mortgage rates citing sources when the user asks about current rates.\n\n"

    "  U.S. Home Loans:\n"
    "- Conventional loans\n"
    "- FHA loans (Federal Housing Administration)\n"
    "- VA loans (for veterans)\n"
    "- USDA loans (for rural housing)\n"
    "- Jumbo loans\n"
    "- Fixed-rate vs Adjustable-rate mortgages (ARM)\n"
    "- Pre-approval, down payments, escrow, closing costs\n\n"

    "  Mortgage Finance Topics:\n"
    "- Loan-to-Value (LTV) ratio\n"
    "- Debt-to-Income (DTI) ratio\n"
    "- Mortgage insurance (PMI, MIP)\n"
    "- Interest rates and amortization\n"
    "- Credit score impact on loan approval\n"
    "- Refinance options\n\n"

    "  Personal Loans (U.S.):\n"
    "- Secured vs unsecured loans\n"
    "- Bank, credit union, and online lenders\n"
    "- APR, fees, repayment terms\n"
    "- Loan consolidation\n\n"

    "  U.S. Regulations and Assistance:\n"
    "- Fannie Mae & Freddie Mac\n"
    "- CFPB guidelines\n"
    "- HUD programs\n"
    "- First-time homebuyer assistance\n"
    "- Loan modification and foreclosure help\n\n"

    "You are allowed to look up or simulate real-time values when relevant to U.S. housing finance or loan queries. "
    "Politely refuse to answer any question that is not about U.S. loans, mortgages, or housing finance."
)

EMAIL_BODY = (
    "Hi,\n\n"
    "Thank you for completing the pre-approval form. "
    "An Assurent Home Loan Officer will review your details and reach out to you shortly with the next steps.\n\n"
    "We appreciate your trust in Assurent Home Loans.\n\n"
    "Best regards,\n"
    "Team Assurent Home Loans"
)







