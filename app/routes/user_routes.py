from fastapi import APIRouter, HTTPException
from typing import List
from app.models import User, Chat
from app.database import user_collection, chat_collection
from collections import defaultdict
message_histories = defaultdict(list)

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
    chats = list(
        chat_collection.find(
            {"email": email, "message": {"$exists": True, "$ne": ""}},  # Only docs with message
            {"_id": 0}
        )
    )
    return chats
@router.delete("/clear-history/{email}")
async def clear_history(email: str):
    if email in message_histories:
        del message_histories[email]
        return {"message": f"History cleared for {email}"}
    return {"message": "No history found for this email"}