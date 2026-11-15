
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.agents.booking_agent import BookingAgent, send_message
from app.models import Event, User, Venue


@pytest.fixture
def booking_event(db_session):
    db = db_session

    user = User(
        name="Booking Test User",
        email=f"booking-{uuid.uuid4().hex}@example.com",
        hashed_password="test-hash",
        role="attendee",
    )

    venue = Venue(
        name="Booking Test Hall",
        location="Colombo",
        capacity=100,
        hourly_rate=1000,
    )

    db.add_all([user, venue])
    db.flush()

    event = Event(
        title="Booking Agent Test Event",
        category="Technology",
        start_time=datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30),
        end_time=datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30, hours=3),
        status="published",
        ticket_price=2500,
        ticket_quantity=10,
        reserved_quantity=0,
        venue_id=venue.id,
        organizer_id=user.id,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def reserve(db, event_id, quantity):
    request = send_message(
        db=db,
        sender="TestUser",
        receiver="BookingAgent",
        performative="REQUEST",
        content={
            "action": "reserve_tickets",
            "event_id": event_id,
            "quantity": quantity,
        },
        conversation_id=str(uuid.uuid4()),
    )

    reply = BookingAgent().handle_message(db, request)
    db.commit()

    return reply


def test_successful_reservation(db_session, booking_event):
    reply = reserve(db_session, booking_event.id, 2)

    assert reply.performative == "AGREE"

    content = json.loads(reply.content)
    assert content["quantity"] == 2
    assert content["total_amount"] == 5000

    db_session.refresh(booking_event)
    assert booking_event.reserved_quantity == 2


def test_insufficient_inventory(db_session, booking_event):
    reply = reserve(db_session, booking_event.id, 11)

    assert reply.performative == "REFUSE"

    db_session.refresh(booking_event)
    assert booking_event.reserved_quantity == 0


def test_zero_quantity_rejected(db_session, booking_event):
    reply = reserve(db_session, booking_event.id, 0)

    assert reply.performative == "REFUSE"

    db_session.refresh(booking_event)
    assert booking_event.reserved_quantity == 0


def test_unpublished_event_rejected(db_session, booking_event):
    booking_event.status = "draft"
    db_session.commit()

    reply = reserve(db_session, booking_event.id, 1)

    assert reply.performative == "REFUSE"


def test_multiple_reservations_respect_capacity(db_session, booking_event):
    first = reserve(db_session, booking_event.id, 7)
    second = reserve(db_session, booking_event.id, 4)

    assert first.performative == "AGREE"
    assert second.performative == "REFUSE"

    db_session.refresh(booking_event)
    assert booking_event.reserved_quantity == 7
