import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
mongo_url = os.getenv("MONGODB_URI")

if not mongo_url:
    raise RuntimeError("MONGODB_URI not set in .env")

mongo_client = MongoClient(mongo_url)
db = mongo_client["chatbotDB"]
user_collection = db["users"]
chat_collection = db["chats"]
admin_collection = db["admins"]
pre_approvals_collection = db["pre_approval"]
