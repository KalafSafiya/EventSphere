
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.csrf import verify_csrf
from app.database import get_db
from app.models import PrivateHire, User
from app.agents.booking_agent import send_message
from app.agents.dispatcher import dispatch_message

router = APIRouter(
    prefix="/private-hires",
    tags=["Private Hires"]
)


class PrivateHireRequest(BaseModel):
    venue_id: int
    start_time: datetime
    end_time: datetime
    purpose: str = Field(min_length=3, max_length=255)
    guest_count: int = Field(gt=0)


class HireDecision(BaseModel):
    approve: bool


def require_admin(
    user: User = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user


@router.post(
    "/request",
    dependencies=[Depends(verify_csrf)]
)
def request_private_hire(
    payload: PrivateHireRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    request = send_message(
        db=db,
        sender="PrivateHireAPI",
        receiver="VenueAgent",
        performative="REQUEST",
        content={
            "action": "request_private_hire",
            "user_id": user.id,
            "venue_id": payload.venue_id,
            "start_time": payload.start_time.isoformat(),
            "end_time": payload.end_time.isoformat(),
            "purpose": payload.purpose,
            "guest_count": payload.guest_count
        },
        conversation_id=str(uuid.uuid4())
    )

    reply = dispatch_message(db, request)
    result = json.loads(reply.content)

    if reply.performative == "REFUSE":
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=result
        )

    if reply.performative == "PROPOSE":
        db.commit()
        return {
            "decision": "PROPOSE",
            **result
        }

    if reply.performative not in ("AGREE", "INFORM"):
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=result
        )

    db.commit()

    return {
        "decision": reply.performative,
        **result
    }


@router.get("/my")
def my_private_hires(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    hires = (
        db.query(PrivateHire)
        .filter(PrivateHire.user_id == user.id)
        .order_by(PrivateHire.created_at.desc())
        .all()
    )

    return [
        {
            "id": hire.id,
            "venue_id": hire.venue_id,
            "start_time": hire.start_time,
            "end_time": hire.end_time,
            "purpose": hire.purpose,
            "guest_count": hire.guest_count,
            "total_price": hire.total_price,
            "status": hire.status
        }
        for hire in hires
    ]


@router.get("/pending")
def pending_private_hires(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    hires = (
        db.query(PrivateHire)
        .filter(PrivateHire.status == "pending")
        .order_by(PrivateHire.created_at.asc())
        .all()
    )

    return [
        {
            "id": hire.id,
            "user_id": hire.user_id,
            "venue_id": hire.venue_id,
            "purpose": hire.purpose,
            "guest_count": hire.guest_count,
            "total_price": hire.total_price,
            "start_time": hire.start_time,
            "end_time": hire.end_time
        }
        for hire in hires
    ]


@router.post(
    "/{hire_id}/decision",
    dependencies=[Depends(verify_csrf)]
)
def decide_private_hire(
    hire_id: int,
    payload: HireDecision,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    hire = db.get(PrivateHire, hire_id)

    if hire is None:
        raise HTTPException(
            status_code=404,
            detail="Private hire request not found"
        )

    if hire.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="This request has already been decided"
        )

    hire.status = (
        "confirmed" if payload.approve else "rejected"
    )

    db.commit()

    return {
        "private_hire_id": hire.id,
        "status": hire.status,
        "decided_by": admin.id
    }
