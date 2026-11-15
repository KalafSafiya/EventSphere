
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.booking_agent import BookingAgent, send_message
from app.auth import get_current_user
from app.csrf import verify_csrf
from app.database import get_db
from app.models import Booking, User
from app.schemas import BookingCreate, BookingResponse
from sqlalchemy import update
from app.models import Event
from app.agents.waitlist_agent import WaitlistAgent

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)]
)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conversation_id = str(uuid.uuid4())

    request_message = send_message(
        db=db,
        sender=f"User:{user.id}",
        receiver="BookingAgent",
        performative="REQUEST",
        content={
            "action": "reserve_tickets",
            "event_id": booking_data.event_id,
            "quantity": booking_data.quantity
        },
        conversation_id=conversation_id
    )

    reply = BookingAgent().handle_message(db, request_message)
    result = json.loads(reply.content)

    if reply.performative != "AGREE":
        db.commit()  # Preserve REFUSE messages
        raise HTTPException(
            status_code=409,
            detail=result
        )

    booking = Booking(
        user_id=user.id,
        event_id=booking_data.event_id,
        quantity=booking_data.quantity,
        total_amount=result["total_amount"],
        status="pending"
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking



@router.post(
    "/{booking_id}/cancel",
    dependencies=[Depends(verify_csrf)]
)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Atomically claim a cancellable booking.
    result = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id,
        Booking.status.in_(["pending", "confirmed"])
    ).update(
        {Booking.status: "cancelled"},
        synchronize_session=False
    )

    if result != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Booking not found or already cancelled"
        )

    booking = db.get(Booking, booking_id)
    event = db.get(Event, booking.event_id)

    # Release the inventory reserved by this booking.
    released = db.execute(
        update(Event)
        .where(
            Event.id == booking.event_id,
            Event.reserved_quantity >= booking.quantity
        )
        .values(
            reserved_quantity=Event.reserved_quantity - booking.quantity
        )
    )

    if released.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not release reserved inventory"
        )

    # A confirmed booking may already have QR tickets.
    # Invalidate them before offering the seats again.
    from app.models import Ticket

    db.query(Ticket).filter(
        Ticket.booking_id == booking.id,
        Ticket.status == "valid"
    ).update(
        {Ticket.status: "cancelled"},
        synchronize_session=False
    )

    conversation_id = str(uuid.uuid4())

    request_message = send_message(
        db=db,
        sender="BookingAgent",
        receiver="WaitlistAgent",
        performative="REQUEST",
        content={
            "action": "process_available_tickets",
            "event_id": booking.event_id
        },
        conversation_id=conversation_id
    )

    reply = WaitlistAgent().handle_message(db, request_message)
    offer_result = json.loads(reply.content)

    db.commit()

    return {
        "message": "Booking cancelled successfully",
        "booking_id": booking.id,
        "released_tickets": booking.quantity,
        "waitlist_result": offer_result
    }
