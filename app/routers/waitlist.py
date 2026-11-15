
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.agents.waitlist_agent import WaitlistAgent
from app.auth import get_current_user
from app.csrf import verify_csrf
from app.database import get_db
from app.models import User, WaitlistEntry
from app.schemas import WaitlistCreate, WaitlistResponse
from datetime import datetime, timezone
from sqlalchemy import update
from app.models import Booking, Event

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post(
    "/",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)]
)
def join_waitlist(
    data: WaitlistCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    request_message = send_message(
        db=db,
        sender=f"User:{user.id}",
        receiver="WaitlistAgent",
        performative="REQUEST",
        content={
            "action": "join_waitlist",
            "event_id": data.event_id,
            "user_id": user.id,
            "quantity": data.quantity
        },
        conversation_id=str(uuid.uuid4())
    )

    reply = WaitlistAgent().handle_message(
        db, request_message
    )

    result = json.loads(reply.content)

    if reply.performative != "AGREE":
        db.commit()
        raise HTTPException(
            status_code=409,
            detail=result
        )

    entry = db.get(
        WaitlistEntry,
        result["waitlist_id"]
    )

    db.commit()
    db.refresh(entry)

    return entry


@router.get("/my", response_model=list[WaitlistResponse])
def my_waitlist(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.user_id == user.id)
        .order_by(WaitlistEntry.created_at.desc())
        .all()
    )




@router.post(
    "/{waitlist_id}/accept",
    dependencies=[Depends(verify_csrf)]
)
def accept_waitlist_offer(
    waitlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Atomically claim the offer so it cannot be accepted twice.
    result = db.execute(
        update(WaitlistEntry)
        .where(
            WaitlistEntry.id == waitlist_id,
            WaitlistEntry.user_id == user.id,
            WaitlistEntry.status == "offered",
            WaitlistEntry.offer_expires_at > now
        )
        .values(status="accepted")
        .execution_options(synchronize_session=False)
    )

    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Offer not found, expired, or already accepted"
        )

    entry = db.get(WaitlistEntry, waitlist_id)
    event = db.get(Event, entry.event_id)

    if event is None or event.status != "published" or event.start_time <= now:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Event is no longer available"
        )

    booking = Booking(
        user_id=user.id,
        event_id=entry.event_id,
        quantity=entry.quantity,
        total_amount=round(event.ticket_price * entry.quantity, 2),
        status="pending"
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "message": "Waitlist offer accepted",
        "booking_id": booking.id,
        "event_id": booking.event_id,
        "quantity": booking.quantity,
        "total_amount": booking.total_amount,
        "status": booking.status
    }

