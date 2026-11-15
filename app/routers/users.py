
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.security import hash_password
from typing import Literal
from pydantic import BaseModel

from app.auth import require_admin
from app.csrf import verify_csrf


router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    email = str(user_data.email).lower()

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = User(
        name=user_data.name,
        email=email,
        hashed_password=hash_password(user_data.password),
        role="attendee"
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return new_user


class StaffRoleUpdate(BaseModel):
    role: Literal["staff", "attendee"]


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(verify_csrf)]
)
def update_staff_role(
    user_id: int,
    role_data: StaffRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Cannot modify an administrator's role"
        )

    user.role = role_data.role

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user


@router.get(
    "/",
    response_model=list[UserResponse]
)
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return (
        db.query(User)
        .order_by(User.id)
        .all()
    )