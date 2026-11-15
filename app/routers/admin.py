
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import (
    User, Venue, Event, Booking, Payment,
    Ticket, WaitlistEntry, Notification,
    PrivateHire, AgentMessage
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Analytics"]
)


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    booking_statuses = dict(
        db.query(Booking.status, func.count(Booking.id))
        .group_by(Booking.status)
        .all()
    )

    payment_statuses = dict(
        db.query(Payment.status, func.count(Payment.id))
        .group_by(Payment.status)
        .all()
    )

    revenue = (
        db.query(func.sum(Payment.amount))
        .filter(Payment.status == "success")
        .scalar()
        or 0
    )

    return {
        "users": db.query(User).count(),
        "venues": db.query(Venue).count(),
        "events": db.query(Event).count(),
        "bookings": db.query(Booking).count(),
        "tickets": db.query(Ticket).count(),
        "waitlist_entries": db.query(WaitlistEntry).count(),
        "notifications": db.query(Notification).count(),
        "private_hires": db.query(PrivateHire).count(),
        "agent_messages": db.query(AgentMessage).count(),
        "revenue": round(float(revenue), 2),
        "booking_statuses": booking_statuses,
        "payment_statuses": payment_statuses
    }


@router.get("/agent-logs")
def agent_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    messages = (
        db.query(AgentMessage)
        .order_by(
            AgentMessage.created_at.desc(),
            AgentMessage.id.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []

    for message in messages:
        try:
            content = json.loads(message.content)
        except (TypeError, ValueError):
            content = message.content

        result.append({
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender": message.sender,
            "receiver": message.receiver,
            "performative": message.performative,
            "content": content,
            "created_at": message.created_at
        })

    return {
        "total": db.query(AgentMessage).count(),
        "limit": limit,
        "offset": offset,
        "messages": result
    }


@router.get("/recent-bookings")
def recent_bookings(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    bookings = (
        db.query(Booking)
        .order_by(
            Booking.created_at.desc(),
            Booking.id.desc()
        )
        .limit(20)
        .all()
    )

    return [
        {
            "id": booking.id,
            "user_id": booking.user_id,
            "event_id": booking.event_id,
            "quantity": booking.quantity,
            "total_amount": booking.total_amount,
            "status": booking.status,
            "created_at": booking.created_at
        }
        for booking in bookings
    ]
