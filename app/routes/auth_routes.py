from fastapi import APIRouter, HTTPException
from app.models import Token
from app.database import user_collection
from openai import OpenAI
import os
import httpx

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
google_client_id = os.getenv("GOOGLE_CLIENT_ID")

@router.post("/verify-token")
async def verify_token(data: Token):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={data.token}")
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = response.json()
    if payload["aud"] != google_client_id:
        raise HTTPException(status_code=403, detail="Invalid client ID")

    if not user_collection.find_one({"email": payload["email"]}):
        user_collection.insert_one({
            "name": payload.get("name", ""),
            "email": payload["email"]
        })

    return {
        "email": payload["email"],
        "name": payload.get("name", ""),
        "picture": payload.get("picture", ""),
        "sub": payload["sub"]
    }