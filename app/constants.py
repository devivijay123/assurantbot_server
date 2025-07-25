PREAPPROVAL_FIELDS = [
    {"key": "borrower_name", "question": "Please enter Borrower First Name and Last Name."},
    {"key": "co_borrower_name", "question": "Co-Borrower First Name & Last Name (If applicable)."},
    {"key": "email", "question": "Email Address", "validate": lambda v: "@" in v and "." in v},
    {"key": "phone", "question": "Phone Number", "validate": lambda v: v.isdigit() and len(v) >= 10},
    {"key": "purchase_price", "question": "Purchase Price", "validate": lambda v: v.replace(",", "").replace(".", "").isdigit()},
    {"key": "loan_amount", "question": "Loan Amount", "validate": lambda v: v.replace(",", "").replace(".", "").isdigit()},
    {"key": "down_payment", "question": "Down Payment (The source for these funds should be readily accessible such as cash, stock, 401K, CDs, etc.)"},
    {"key": "property_address", "question": "Property Address (put TBD if unknown)"},
    {"key": "gross_pay", "question": "Average Annual Documented Gross Pay over the last 2 years"},
    {"key": "foreign_assets", "question": "Do you declare foreign assets and investments in your tax returns?"},
    {"key": "credit_score", "question": "What is the average credit score reflected across all your banks and credit cards (Don’t use Credit Karma)?"}
]