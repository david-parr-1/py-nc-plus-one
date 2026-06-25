import bcrypt
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta


load_dotenv()


JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_SECRET = os.getenv("JWT_SECRET")


def hash_password(unhashed_password: str) -> str:
    return bcrypt.hashpw(unhashed_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
