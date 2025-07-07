from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
mongodb_uri=os.getenv("MONGODB_URI")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY not set in .env")

# OpenAI client (new SDK)
client = OpenAI(api_key=openai_api_key)

# FastAPI app
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=    "http://localhost:5174",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
mongo_client = MongoClient(mongodb_uri)
db = mongo_client["chatbotDB"]
user_collection = db["users"]
chat_collection = db["chats"]

# Pydantic models
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

# Endpoint to start a chat session
@app.post("/start-chat")
async def start_chat(user: User):
    if not user.email or not user.name:
        raise HTTPException(status_code=400, detail="Email and name required")
    if not user_collection.find_one({"email": user.email}):
        user_collection.insert_one(user.dict())
    return {"message": "User chat started"}

# Endpoint to handle chat messages
@app.post("/chat")
async def chat(input: ChatInput):
    chat_collection.insert_one(input.dict())

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Assurant Home Loans. You specialize in helping customers with Mortgage applications and pre-approval processes,Home loan products (conventional, FHA, VA, USDA loans), Interest rates and payment calculations, Refinancing options, Down payment assistance programs, Credit requirements and improvement tips, Home buying process guidance, Loan documentation requirements. Always be professional, helpful, and provide accurate information about home loans and mortgages. If you don't know specific current rates or policies, advise the customer to contact Assurant directly for the most up-to-date information.You must not answer questions outside of the mortgage, home loan, or credit topics under any circumstances.Always be professional, helpful, and provide accurate, general guidance about home loans and mortgages. If you are asked questions *outside of these topics, respond with Please ask questions related to mortgage loans, credit, or home buying assistance.If you are unsure about current rates or policies, respond with Summarize"},
                {"role": "user", "content": input.message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        bot_reply = response.choices[0].message.content.strip()

        chat_collection.insert_one({
            "email": input.email,
            "message": bot_reply,
            "sender": "bot"
        })

        return {"reply": bot_reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin: Get all users
@app.get("/admin/users", response_model=List[User], tags=["Admin"])
def get_all_users():
    users = list(user_collection.find({}, {"_id": 0, "name": 1, "email": 1}))
    return users

# Admin: Get user chat history
@app.get("/admin/user-history/{email}", response_model=List[Chat], tags=["Admin"])
def get_user_history(email: str):
    chats = list(chat_collection.find({"email": email}, {"_id": 0}))
    return chats