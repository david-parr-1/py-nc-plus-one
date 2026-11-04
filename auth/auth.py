import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from dotenv import load_dotenv

from src.utils import fetch_ssm_parameter

load_dotenv()


JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "30")) or fetch_ssm_parameter(
    "/nc-plus-one/JWT_EXPIRY_MINUTES"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or fetch_ssm_parameter(
    "/nc-plus-one/JWT_ALGORITHM"
)
JWT_SECRET = os.getenv("JWT_SECRET") or fetch_ssm_parameter("/nc-plus-one/JWT_SECRET")


def hash_password(unhashed_password: str) -> str:
    return bcrypt.hashpw(unhashed_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
