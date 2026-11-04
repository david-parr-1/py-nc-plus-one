from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from db.configuration import JWTConfig


def hash_password(unhashed_password: str) -> str:
    return bcrypt.hashpw(unhashed_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    config = JWTConfig.get_config()
    expire = datetime.now(UTC) + timedelta(minutes=config.jwt_expiry_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)
