
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user_routes, admin_routes, chat_routes, auth_routes, mortgage_routes, amortization_routes, url_routes, user_chat_routes



app = FastAPI()

origins = [
    "https://assurantchatbotapp.onrender.com"
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Not recommended for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(chat_routes.router)
app.include_router(admin_routes.router)
app.include_router(mortgage_routes.router)
app.include_router(amortization_routes.router)
app.include_router(url_routes.router)
app.include_router(user_chat_routes.router)