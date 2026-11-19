from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

from db.configuration import JWTConfig
from src.logging_config import get_logger

logger = get_logger(__name__)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(unhashed_password: str) -> str:
    return bcrypt.hashpw(unhashed_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    config = JWTConfig.get_config()
    expiry_minutes = float(config.jwt_expiry_minutes)
    expire = datetime.now(UTC) + timedelta(minutes=expiry_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def get_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        logger.info("Parsing token...")
        jwt_config = JWTConfig.get_config()
        payload = jwt.decode(
            token, jwt_config.jwt_secret, algorithms=[jwt_config.jwt_algorithm]
        )

        logger.info("Token parsed successfully.")
        return int(payload["sub"])

    except jwt.ExpiredSignatureError:
        logger.error("Token has expired.")
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        logger.error("Token is invalid.")
        raise HTTPException(status_code=401, detail="Token is invalid")
