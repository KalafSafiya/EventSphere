
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.agents.booking_agent import send_message
from app.agents.ticket_agent import TicketAgent
from app.database import Base
from app.models import Booking, Event, Ticket, User, Venue


def test_ticket_checkin_only_once():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        with Session(engine) as db:
            user = User(
                name="Test Attendee",
                email="checkin-test@example.com",
                hashed_password="test-hash",
                role="attendee",
            )
            venue = Venue(
                name="Test Hall",
                location="Colombo",
                capacity=100,
                hourly_rate=1000,
            )
            db.add_all([user, venue])
            db.flush()

            event = Event(
                title="Check-in Test Event",
                category="Technology",
                start_time=now - timedelta(minutes=30),
                end_time=now + timedelta(hours=2),
                status="published",
                ticket_price=1000,
                ticket_quantity=50,
                venue_id=venue.id,
                organizer_id=user.id,
            )
            db.add(event)
            db.flush()

            booking = Booking(
                user_id=user.id,
                event_id=event.id,
                quantity=1,
                total_amount=1000,
                status="confirmed",
            )
            db.add(booking)
            db.flush()

            ticket = Ticket(
                booking_id=booking.id,
                event_id=event.id,
                qr_token="test-unique-qr-token-12345",
                status="valid",
            )
            db.add(ticket)
            db.flush()

            agent = TicketAgent()

            first_request = send_message(
                db,
                sender="Staff:1",
                receiver="TicketAgent",
                performative="REQUEST",
                content={
                    "action": "check_in",
                    "qr_token": ticket.qr_token,
                    "event_id": event.id,
                },
                conversation_id="checkin-test-1",
            )

            first_reply = agent.handle_checkin(db, first_request)
            assert first_reply.performative == "INFORM"

            db.commit()

            second_request = send_message(
                db,
                sender="Staff:1",
                receiver="TicketAgent",
                performative="REQUEST",
                content={
                    "action": "check_in",
                    "qr_token": ticket.qr_token,
                    "event_id": event.id,
                },
                conversation_id="checkin-test-2",
            )

            second_reply = agent.handle_checkin(db, second_request)

            assert second_reply.performative == "REFUSE"
            assert "already checked in" in json.loads(
                second_reply.content
            )["reason"].lower()

            db.refresh(ticket)
            assert ticket.status == "used"
            assert ticket.checked_in_at is not None

    finally:
        engine.dispose()
