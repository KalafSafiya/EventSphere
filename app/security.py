
import os

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    if os.getenv("APP_ENV") == "production":
        raise RuntimeError("SECRET_KEY must be set in production")
    SECRET_KEY = "dev-only-change-before-deployment"
serializer = URLSafeTimedSerializer(SECRET_KEY, salt="eventsphere-session")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_session_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def verify_session_token(token: str) -> int | None:
    try:
        data = serializer.loads(token, max_age=3600)
        return int(data["user_id"])
    except (BadSignature, SignatureExpired, KeyError, ValueError, TypeError):
        return None
