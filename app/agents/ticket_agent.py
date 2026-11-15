
import json
import secrets

from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.models import AgentMessage, Booking, Ticket
from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from app.models import Event


class TicketAgent:

    def handle_message(
        self,
        db: Session,
        message: AgentMessage
    ):
        content = json.loads(message.content)

        if (
            message.performative != "REQUEST"
            or content.get("action") != "issue_tickets"
        ):
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Unsupported request"}
            )

        booking = db.get(Booking, content["booking_id"])

        if booking is None or booking.status != "confirmed":
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Booking is not confirmed"}
            )

        existing = (
            db.query(Ticket)
            .filter(Ticket.booking_id == booking.id)
            .count()
        )

        if existing > 0:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Tickets already issued"}
            )

        tickets = []

        for _ in range(booking.quantity):
            ticket = Ticket(
                booking_id=booking.id,
                event_id=booking.event_id,
                qr_token=secrets.token_urlsafe(32),
                status="valid"
            )
            db.add(ticket)
            tickets.append(ticket)

        db.flush()

        return self.reply(
            db, message, "INFORM",
            {
                "booking_id": booking.id,
                "ticket_ids": [t.id for t in tickets],
                "quantity": len(tickets)
            }
        )

    def reply(self, db, original, performative, content):
        return send_message(
            db=db,
            sender="TicketAgent",
            receiver=original.sender,
            performative=performative,
            content=content,
            conversation_id=original.conversation_id
        )



    def handle_checkin(self, db: Session, message: AgentMessage):
        content = json.loads(message.content)

        if (
            message.performative != "REQUEST"
            or content.get("action") != "check_in"
        ):
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Unsupported check-in request"}
            )

        token = content.get("qr_token")
        event_id = content.get("event_id")

        ticket = db.query(Ticket).filter(
            Ticket.qr_token == token
        ).first()

        if ticket is None:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Invalid QR ticket"}
            )

        if ticket.event_id != event_id:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Ticket belongs to another event"}
            )

        booking = db.get(Booking, ticket.booking_id)
        event = db.get(Event, ticket.event_id)

        if booking is None or booking.status != "confirmed":
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Booking is not confirmed"}
            )

        if event is None or event.status != "published":
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Event is not active"}
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Check-in opens 2 hours before and closes 1 hour after event end.
        if not (
            event.start_time - timedelta(hours=2)
            <= now
            <= event.end_time + timedelta(hours=1)
        ):
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Outside check-in window"}
            )

        # Conditional UPDATE guarantees only one successful check-in.
        result = db.execute(
            update(Ticket)
            .where(
                Ticket.id == ticket.id,
                Ticket.status == "valid",
                Ticket.checked_in_at.is_(None)
            )
            .values(
                status="used",
                checked_in_at=now
            )
            .execution_options(synchronize_session=False)
        )

        if result.rowcount != 1:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Ticket already checked in or cancelled"}
            )

        return self.reply(
            db, message, "INFORM",
            {
                "ticket_id": ticket.id,
                "event_id": event_id,
                "checked_in_at": now.isoformat()
            }
        )
