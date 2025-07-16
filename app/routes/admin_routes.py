from fastapi import APIRouter, HTTPException
from typing import List
from app.models import AdminLogin, User, Chat
from app.database import admin_collection, user_collection, chat_collection
from app.utils import verify_password, create_access_token

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[User])
def get_all_users():
    users = list(user_collection.find({}, {"_id": 0, "name": 1, "email": 1}))
    return users

@router.get("/user-history/{email}", response_model=List[Chat])
def get_user_history(email: str):
    chats = list(chat_collection.find({"email": email}, {"_id": 0}))
    return chats

@router.post("/login")
def admin_login(credentials: AdminLogin):
    admin = admin_collection.find_one({"email": credentials.email})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not verify_password(credentials.password, admin["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_access_token(credentials.email)
    return {"access_token": token, "token_type": "bearer"}
