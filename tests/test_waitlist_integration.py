
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.agents.booking_agent import send_message
from app.agents.dispatcher import dispatch_message
from app.models import (
    AgentMessage,
    Booking,
    Event,
    Notification,
    User,
    Venue,
    WaitlistEntry,
)
from app.routers.bookings import cancel_booking


@pytest.fixture
def waitlist_setup(db_session):
    owner = User(
        name="Booking Owner",
        email="waitlist-owner@example.com",
        hashed_password="test-hash",
        role="attendee",
    )

    waiting_user = User(
        name="Waiting User",
        email="waitlist-user@example.com",
        hashed_password="test-hash",
        role="attendee",
    )

    venue = Venue(
        name="Waitlist Test Hall",
        location="Colombo",
        capacity=100,
        hourly_rate=1000,
    )

    db_session.add_all([owner, waiting_user, venue])
    db_session.flush()

    start = datetime.now(timezone.utc).replace(
        tzinfo=None
    ) + timedelta(days=30)

    event = Event(
        title="Waitlist Integration Event",
        category="Technology",
        start_time=start,
        end_time=start + timedelta(hours=3),
        status="published",
        ticket_price=2500,
        ticket_quantity=2,
        reserved_quantity=2,
        venue_id=venue.id,
        organizer_id=owner.id,
    )

    db_session.add(event)
    db_session.flush()

    booking = Booking(
        user_id=owner.id,
        event_id=event.id,
        quantity=2,
        total_amount=5000,
        status="confirmed",
    )

    waitlist_entry = WaitlistEntry(
        user_id=waiting_user.id,
        event_id=event.id,
        quantity=1,
        status="waiting",
    )

    db_session.add_all([booking, waitlist_entry])
    db_session.commit()

    return owner, waiting_user, event, booking, waitlist_entry


def send_agent_request(db, action, **extra):
    request = send_message(
        db=db,
        sender="IntegrationTest",
        receiver="WaitlistAgent",
        performative="REQUEST",
        content={"action": action, **extra},
        conversation_id=str(uuid.uuid4()),
    )

    reply = dispatch_message(db, request)
    db.commit()

    return reply


def test_cancellation_releases_and_offers_tickets(
    db_session, waitlist_setup
):
    owner, waiting_user, event, booking, entry = waitlist_setup

    result = cancel_booking(
        booking_id=booking.id,
        db=db_session,
        user=owner,
    )

    db_session.refresh(booking)
    db_session.refresh(event)
    db_session.refresh(entry)

    assert booking.status == "cancelled"
    assert result["released_tickets"] == 2
    assert result["waitlist_result"]["offers_created"] == 1

    assert entry.status == "offered"
    assert entry.offer_expires_at is not None

    # Two tickets released, one reserved for the offer.
    assert event.reserved_quantity == 1


def test_cancellation_creates_waitlist_notification(
    db_session, waitlist_setup
):
    owner, waiting_user, event, booking, entry = waitlist_setup

    cancel_booking(
        booking_id=booking.id,
        db=db_session,
        user=owner,
    )

    notification = db_session.query(Notification).filter(
        Notification.user_id == waiting_user.id,
        Notification.notification_type == "waitlist_offer",
    ).first()

    assert notification is not None
    assert notification.title == "Tickets Available!"


def test_agent_messages_recorded(
    db_session, waitlist_setup
):
    owner, waiting_user, event, booking, entry = waitlist_setup

    cancel_booking(
        booking_id=booking.id,
        db=db_session,
        user=owner,
    )

    messages = db_session.query(AgentMessage).all()

    assert any(
        message.receiver == "WaitlistAgent"
        for message in messages
    )

    assert any(
        message.receiver == "NotificationAgent"
        for message in messages
    )

    assert any(
        message.sender == "NotificationAgent"
        for message in messages
    )


def test_expired_offer_releases_inventory(
    db_session, waitlist_setup
):
    owner, waiting_user, event, booking, entry = waitlist_setup

    # Simulate cancellation and creation of a waitlist offer.
    cancel_booking(
        booking_id=booking.id,
        db=db_session,
        user=owner,
    )

    db_session.refresh(entry)

    # Simulate an offer whose 15-minute deadline has passed.
    entry.offer_expires_at = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        - timedelta(minutes=1)
    )
    db_session.commit()

    reply = send_agent_request(
        db_session,
        "expire_offers",
    )

    db_session.refresh(event)
    db_session.refresh(entry)

    assert reply.performative == "INFORM"
    assert json.loads(reply.content)["expired_offers"] == 1

    assert entry.status == "expired"
    assert event.reserved_quantity == 0


def test_expiration_creates_notification(
    db_session, waitlist_setup
):
    owner, waiting_user, event, booking, entry = waitlist_setup

    cancel_booking(
        booking_id=booking.id,
        db=db_session,
        user=owner,
    )

    entry.offer_expires_at = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        - timedelta(minutes=1)
    )
    db_session.commit()

    send_agent_request(
        db_session,
        "expire_offers",
    )

    notification = db_session.query(Notification).filter(
        Notification.user_id == waiting_user.id,
        Notification.notification_type == "offer_expired",
    ).first()

    assert notification is not None
    assert notification.title == "Waitlist Offer Expired"


def test_expiration_is_not_processed_twice(
    db_session, waitlist_setup
):
    owner, waiting_user, event, booking, entry = waitlist_setup

    cancel_booking(
        booking_id=booking.id,
        db=db_session,
        user=owner,
    )

    entry.offer_expires_at = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        - timedelta(minutes=1)
    )
    db_session.commit()

    first = send_agent_request(db_session, "expire_offers")
    second = send_agent_request(db_session, "expire_offers")

    assert json.loads(first.content)["expired_offers"] == 1
    assert json.loads(second.content)["expired_offers"] == 0

    db_session.refresh(event)
    assert event.reserved_quantity == 0
