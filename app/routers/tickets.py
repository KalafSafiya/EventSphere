
import io
import json
import uuid

import qrcode
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.agents.ticket_agent import TicketAgent
from app.auth import get_current_user
from app.csrf import verify_csrf
from app.database import get_db
from app.models import Booking, Ticket, User

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "/issue/{booking_id}",
    dependencies=[Depends(verify_csrf)]
)
def issue_tickets(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    booking = db.get(Booking, booking_id)

    if booking is None or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    request_message = send_message(
        db=db,
        sender=f"User:{user.id}",
        receiver="TicketAgent",
        performative="REQUEST",
        content={
            "action": "issue_tickets",
            "booking_id": booking_id
        },
        conversation_id=str(uuid.uuid4())
    )

    reply = TicketAgent().handle_message(db, request_message)
    result = json.loads(reply.content)

    db.commit()

    if reply.performative == "REFUSE":
        raise HTTPException(status_code=409, detail=result)

    return result


@router.get("/my")
def my_tickets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return (
        db.query(Ticket)
        .join(Booking, Ticket.booking_id == Booking.id)
        .filter(Booking.user_id == user.id)
        .all()
    )


@router.get("/{ticket_id}/qr")
def get_ticket_qr(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    ticket = (
        db.query(Ticket)
        .join(Booking, Ticket.booking_id == Booking.id)
        .filter(
            Ticket.id == ticket_id,
            Booking.user_id == user.id
        )
        .first()
    )

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    img = qrcode.make(ticket.qr_token)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")
