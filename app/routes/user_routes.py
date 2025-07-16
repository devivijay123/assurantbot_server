from fastapi import APIRouter, HTTPException
from typing import List
from app.models import User, Chat
from app.database import user_collection, chat_collection

router = APIRouter(prefix="/user")

@router.post("/start-chat")
async def start_chat(user: User):
    if not user.email or not user.name:
        raise HTTPException(status_code=400, detail="Email and name required")
    if not user_collection.find_one({"email": user.email}):
        user_collection.insert_one(user.dict())
    return {"message": "User chat started"}

@router.get("/chat-history/{email}", response_model=List[Chat])
async def get_user_chat_history(email: str):
    if not user_collection.find_one({"email": email}):
        raise HTTPException(status_code=404, detail="User not found")
    chats = list(chat_collection.find({"email": email}, {"_id": 0}))
    return chats