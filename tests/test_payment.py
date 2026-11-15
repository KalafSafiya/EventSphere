
import pytest
from datetime import datetime, timedelta, timezone

from app.models import User, Venue, Event, Booking, Payment
from app.routers.payments import simulate_payment
from app.schemas import PaymentRequest
from fastapi import HTTPException


@pytest.fixture
def pending_booking(db_session):
    user = User(
        name="Payment Test User",
        email="payment-test@example.com",
        hashed_password="test-hash",
        role="attendee",
    )

    venue = Venue(
        name="Payment Test Venue",
        location="Colombo",
        capacity=100,
        hourly_rate=1000,
    )

    db_session.add_all([user, venue])
    db_session.flush()

    start = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)

    event = Event(
        title="Payment Test Event",
        category="Technology",
        start_time=start,
        end_time=start + timedelta(hours=3),
        status="published",
        ticket_price=2500,
        ticket_quantity=10,
        reserved_quantity=2,
        venue_id=venue.id,
        organizer_id=user.id,
    )

    db_session.add(event)
    db_session.flush()

    booking = Booking(
        user_id=user.id,
        event_id=event.id,
        quantity=2,
        total_amount=5000,
        status="pending",
    )

    db_session.add(booking)
    db_session.commit()

    return user, event, booking


def test_successful_payment(db_session, pending_booking):
    user, event, booking = pending_booking

    result = simulate_payment(
        booking_id=booking.id,
        payment_data=PaymentRequest(success=True),
        db=db_session,
        user=user,
    )

    db_session.refresh(booking)
    db_session.refresh(event)

    assert result.status == "success"
    assert result.amount == 5000
    assert result.transaction_reference is not None
    assert booking.status == "confirmed"
    assert event.reserved_quantity == 2


def test_failed_payment_releases_inventory(db_session, pending_booking):
    user, event, booking = pending_booking

    result = simulate_payment(
        booking_id=booking.id,
        payment_data=PaymentRequest(success=False),
        db=db_session,
        user=user,
    )

    db_session.refresh(booking)
    db_session.refresh(event)

    assert result.status == "failed"
    assert booking.status == "cancelled"
    assert event.reserved_quantity == 0


def test_duplicate_payment_rejected(db_session, pending_booking):
    user, event, booking = pending_booking

    simulate_payment(
        booking_id=booking.id,
        payment_data=PaymentRequest(success=True),
        db=db_session,
        user=user,
    )

    with pytest.raises(HTTPException) as exc:
        simulate_payment(
            booking_id=booking.id,
            payment_data=PaymentRequest(success=True),
            db=db_session,
            user=user,
        )

    assert exc.value.status_code == 409

    payments = db_session.query(Payment).filter(
        Payment.booking_id == booking.id
    ).all()

    assert len(payments) == 1


def test_payment_by_another_user_rejected(db_session, pending_booking):
    user, event, booking = pending_booking

    another_user = User(
        name="Another User",
        email="another-payment-user@example.com",
        hashed_password="test-hash",
        role="attendee",
    )

    db_session.add(another_user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        simulate_payment(
            booking_id=booking.id,
            payment_data=PaymentRequest(success=True),
            db=db_session,
            user=another_user,
        )

    assert exc.value.status_code == 409

    db_session.refresh(booking)
    assert booking.status == "pending"


def test_payment_for_nonexistent_booking_rejected(db_session, pending_booking):
    user, event, booking = pending_booking

    with pytest.raises(HTTPException) as exc:
        simulate_payment(
            booking_id=999999,
            payment_data=PaymentRequest(success=True),
            db=db_session,
            user=user,
        )

    assert exc.value.status_code == 409
