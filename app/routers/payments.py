

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.csrf import verify_csrf
from app.database import get_db
from app.models import Booking, Event, Payment, User
from app.schemas import PaymentRequest, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/{booking_id}/simulate",
    response_model=PaymentResponse,
    dependencies=[Depends(verify_csrf)]
)
def simulate_payment(
    booking_id: int,
    payment_data: PaymentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Atomically claim a pending booking to prevent repeated payment processing.
    claim = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id,
        Booking.status == "pending"
    ).update(
        {Booking.status: "processing"},
        synchronize_session=False
    )

    if claim != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Booking not found, not owned by you, or already processed"
        )

    booking = db.get(Booking, booking_id)

    payment_status = "success" if payment_data.success else "failed"
    reference = str(uuid.uuid4()) if payment_data.success else None

    payment = Payment(
        booking_id=booking.id,
        amount=booking.total_amount,
        status=payment_status,
        transaction_reference=reference
    )

    db.add(payment)

    if payment_data.success:
        booking.status = "confirmed"
    else:
        booking.status = "cancelled"

        db.execute(
            update(Event)
            .where(
                Event.id == booking.event_id,
                Event.reserved_quantity >= booking.quantity
            )
            .values(
                reserved_quantity=Event.reserved_quantity - booking.quantity
            )
        )

    db.commit()

    return PaymentResponse(
        booking_id=booking.id,
        amount=payment.amount,
        status=payment.status,
        transaction_reference=payment.transaction_reference
    )
