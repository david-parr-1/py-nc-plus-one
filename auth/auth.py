import bcrypt


def hash_password(unhashed_password: str) -> str:
    return bcrypt.hashpw(unhashed_password.encode(), bcrypt.gensalt()).decode()
