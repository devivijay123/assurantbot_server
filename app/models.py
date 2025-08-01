from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str

class ChatInput(BaseModel):
    email: str
    message: str
    sender: str = "user"

class Chat(BaseModel):
    email: str
    message: str
    sender: str

class AdminLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    token: str

class MortgageRequest(BaseModel):
    loanAmount: float
    interestRate: float
    loanTerm: int  # in years

class PreApprovalRequest(BaseModel):
    name: str
    email: str
    income: str
    property_value: str
