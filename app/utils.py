from passlib.context import CryptContext
from jose import jwt
import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
secret_key = "your_secret_key"

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(email: str):
    payload = {
        "sub": email,
        "role": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)