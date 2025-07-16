# from fastapi import FastAPI, HTTPException, APIRouter
# from pydantic import BaseModel
# from pymongo import MongoClient
# import os
# from typing import List
# from dotenv import load_dotenv
# from openai import OpenAI
# from fastapi.middleware.cors import CORSMiddleware
# from passlib.context import CryptContext
# from jose import jwt
# import datetime
# import httpx
# from collections import defaultdict
# # Load environment variables
# load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")
# google_client_id = os.getenv("GOOGLE_CLIENT_ID")
# mongo_url = os.getenv("MONGODB_URI")
# if not openai_api_key:
#     raise RuntimeError("OPENAI_API_KEY not set in .env")
# if not google_client_id:
#     raise RuntimeError("GOOGLE_CLIENT_ID not set in .env")

# # OpenAI client (new SDK)
# client = OpenAI(api_key=openai_api_key)

# ALGORITHM = "HS256"
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# class AdminLogin(BaseModel):
#     email: str
#     password: str

# # FastAPI app
# app = FastAPI()


# # CORS settings
# origins = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     "http://localhost:5174",
#     "http://localhost:5173"
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # MongoDB setup

# mongo_client = MongoClient(mongo_url)

# db = mongo_client["chatbotDB"]
# user_collection = db["users"]
# chat_collection = db["chats"]
# admin_collection = db["admins"]

# import bcrypt
# print(bcrypt.__file__)


# from passlib.context import CryptContext
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# message_histories = defaultdict(list)

# # Pydantic models
# class User(BaseModel):
#     name: str
#     email: str

# class ChatInput(BaseModel):
#     email: str
#     message: str
#     sender: str = "user"

# class Chat(BaseModel):
#     email: str
#     message: str
#     sender: str

# class AdminLogin(BaseModel):
#     email: str
#     password: str

# class Token(BaseModel):
#     token: str

# secret_key = 'your_secret_key'

# SYSTEM_PROMPT = (
#     "You are a U.S. financial assistant that answers only questions related to loans, mortgages, and housing finance. "
#     "You provide accurate, practical information specifically for users in the United States.\n\n"
#     "Always format detailed responses in lists or tables where applicable.\n\n"
#     "You are allowed to fetch and present the latest available mortgage rates using online sources when the user asks about current rates.\n\n"

#     "  U.S. Home Loans:\n"
#     "- Conventional loans\n"
#     "- FHA loans (Federal Housing Administration)\n"
#     "- VA loans (for veterans)\n"
#     "- USDA loans (for rural housing)\n"
#     "- Jumbo loans\n"
#     "- Fixed-rate vs Adjustable-rate mortgages (ARM)\n"
#     "- Pre-approval, down payments, escrow, closing costs\n\n"

#     "  Mortgage Finance Topics:\n"
#     "- Loan-to-Value (LTV) ratio\n"
#     "- Debt-to-Income (DTI) ratio\n"
#     "- Mortgage insurance (PMI, MIP)\n"
#     "- Interest rates and amortization\n"
#     "- Credit score impact on loan approval\n"
#     "- Refinance options\n\n"

#     "  Personal Loans (U.S.):\n"
#     "- Secured vs unsecured loans\n"
#     "- Bank, credit union, and online lenders\n"
#     "- APR, fees, repayment terms\n"
#     "- Loan consolidation\n\n"

#     "  U.S. Regulations and Assistance:\n"
#     "- Fannie Mae & Freddie Mac\n"
#     "- CFPB guidelines\n"
#     "- HUD programs\n"
#     "- First-time homebuyer assistance\n"
#     "- Loan modification and foreclosure help\n\n"

#     "You are allowed to look up or simulate real-time values when relevant to U.S. housing finance or loan queries. "
#     "Politely refuse to answer any question that is not about U.S. loans, mortgages, or housing finance."
# )

# #  Google Token Verification
# @app.post("/verify-token")
# async def verify_token(data: Token):
#     try:
#         print("Token received:", data.token)
#         async with httpx.AsyncClient() as client:


#             response = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={data.token}")
#         print("Google tokeninfo status:", response.status_code)
#         print("Response text:", response.text)
#         if response.status_code != 200:
#             raise HTTPException(status_code=401, detail="Invalid token")

#         payload = response.json()

#         if payload["aud"] != google_client_id:
#             raise HTTPException(status_code=403, detail="Invalid client ID")

#         # Save user if not exists
#         if not user_collection.find_one({"email": payload["email"]}):
#             user_collection.insert_one({
#                 "name": payload.get("name", ""),
#                 "email": payload["email"]
#             })

#         return {
#             "email": payload["email"],
#             "name": payload.get("name", ""),
#             "picture": payload.get("picture", ""),
#             "sub": payload["sub"]
#         }

#     except Exception as e:
#         print("Internal error:", str(e))
#         raise HTTPException(status_code=500, detail=str(e))

# # Endpoint to start a chat session
# @app.post("/start-chat")
# async def start_chat(user: User):
#     if not user.email or not user.name:
#         raise HTTPException(status_code=400, detail="Email and name required")
#     if not user_collection.find_one({"email": user.email}):
#         user_collection.insert_one(user.dict())
#     return {"message": "User chat started"}

# # Endpoint to handle chat messages
# @app.post("/chat")
# async def chat(input: ChatInput):
#     chat_collection.insert_one(input.dict())
#     user_email = input.email
#     user_message = input.message.strip()
#     if not message_histories[user_email]:
#         message_histories[user_email].append({"role": "system", "content": SYSTEM_PROMPT})

#     # Append the current user message
#     message_histories[user_email].append({"role": "user", "content": user_message})

#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=message_histories[user_email],
#             temperature=0.7,
#             max_tokens=300
#         )
#         bot_reply = response.choices[0].message.content.strip()
#         message_histories[user_email].append({"role": "assistant", "content": bot_reply})

#         chat_collection.insert_one({
#             "email": input.email,
#             "message": bot_reply,
#             "sender": "bot"
#         })

#         return {"reply": bot_reply}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Admin: Get all users
# @app.get("/admin/users", response_model=List[User], tags=["Admin"])
# def get_all_users():
#     users = list(user_collection.find({}, {"_id": 0, "name": 1, "email": 1}))
#     return users

# # Admin: Get user chat history
# @app.get("/admin/user-history/{email}", response_model=List[Chat], tags=["Admin"])
# def get_user_history(email: str):
#     chats = list(chat_collection.find({"email": email}, {"_id": 0}))
#     return chats


# @app.post("/admin/login", tags=["Admin"])
# def admin_login(credentials: AdminLogin):
#     print(f"[INFO] Admin login attempt for email: {credentials.email}")

#     try:
#         admin = admin_collection.find_one({"email": credentials.email})
#     except Exception as e:
#         print(f"[ERROR] DB query failed: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error during DB lookup")

#     if not admin:
#         print(f"[WARN] Admin not found: {credentials.email}")
#         raise HTTPException(status_code=404, detail="Admin not found")

#     try:
#         if not pwd_context.verify(credentials.password, admin["password"]):
#             print(f"[WARN] Incorrect password for: {credentials.email}")
#             raise HTTPException(status_code=401, detail="Incorrect password")
#     except Exception as e:
#         print(f"[ERROR] Password verification error: {e}")
#         raise HTTPException(status_code=500, detail="Error verifying password")

#     print(f"[INFO] Password verified for: {credentials.email}")

#     payload = {
#         "sub": credentials.email,
#         "role": "admin",
#         'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
#     }

#     try:
#         token = jwt.encode(payload,  secret_key,algorithm=ALGORITHM)
#         print(f"[INFO] Token generated successfully for: {credentials.email}")
#     except Exception as e:
#         print(f"[ERROR] Token generation failed: {e}")
#         raise HTTPException(status_code=500, detail="Error generating token")

#     return {"access_token": token, "token_type": "bearer"}

# @app.get("/user/chat-history/{email}", response_model=List[Chat])
# async def get_user_chat_history(email: str):
#     if not user_collection.find_one({"email": email}):
#         raise HTTPException(status_code=404, detail="User not found")

#     chats = list(chat_collection.find({"email": email}, {"_id": 0}))
#     return chats



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user_routes, admin_routes, chat_routes, auth_routes

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(chat_routes.router)
app.include_router(admin_routes.router)