
import secrets
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, UserResponse, MessageResponse
from app.security import (
    create_session_token,
    verify_password,
)


from app.csrf import verify_csrf

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=MessageResponse)
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    email = str(credentials.email).lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(
        credentials.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_session_token(user.id)

    response.set_cookie(
        key="eventsphere_session",
        value=token,
        httponly=True,
        secure=os.getenv("APP_ENV") == "production",
        samesite="lax",
        max_age=3600,
        path="/"
    )

    # CSRF token for future state-changing authenticated requests
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="eventsphere_csrf",
        value=csrf_token,
        httponly=False,
        secure=os.getenv("APP_ENV") == "production",
        samesite="lax",
        max_age=3600,
        path="/"
    )

    return {"message": "Login successful"}


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/admin-check", response_model=MessageResponse)
def admin_check(current_user: User = Depends(require_admin)):
    return {"message": "Admin access granted"}


@router.post(
    "/logout",
    response_model=MessageResponse,
    dependencies=[Depends(verify_csrf)]
)
def logout(response: Response):
    response.delete_cookie("eventsphere_session", path="/")
    response.delete_cookie("eventsphere_csrf", path="/")
    return {"message": "Logged out"}