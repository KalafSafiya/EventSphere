
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.models import AgentMessage, Event, WaitlistEntry
from datetime import timedelta
from sqlalchemy import update


class WaitlistAgent:

    def handle_message(
        self,
        db: Session,
        message: AgentMessage
    ):
        content = json.loads(message.content)

        if message.performative != "REQUEST":
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Unsupported performative"}
            )

        action = content.get("action")

        if action == "join_waitlist":
            return self.join_waitlist(db, message, content)

        if action == "process_available_tickets":
            return self.process_available_tickets(db, message, content)

        if action == "expire_offers":
            return self.expire_offers(db, message)

        return self.reply(
            db, message, "REFUSE",
            {"reason": "Unsupported action"}
        )

    def join_waitlist(self, db, message, content):
        event_id = content.get("event_id")
        user_id = content.get("user_id")
        quantity = content.get("quantity")

        if (
            not isinstance(event_id, int)
            or not isinstance(user_id, int)
            or not isinstance(quantity, int)
            or quantity < 1
            or quantity > 10
        ):
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Invalid waitlist request"}
            )

        event = db.get(Event, event_id)

        if event is None:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Event not found"}
            )

        if event.status != "published":
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Event is not published"}
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if event.start_time <= now:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Event has already started"}
            )

        available = (
            event.ticket_quantity - event.reserved_quantity
        )

        if available >= quantity:
            return self.reply(
                db, message, "REFUSE",
                {
                    "reason": "Tickets are available. Book directly.",
                    "available": available
                }
            )

        existing = (
            db.query(WaitlistEntry)
            .filter(
                WaitlistEntry.user_id == user_id,
                WaitlistEntry.event_id == event_id,
                WaitlistEntry.status.in_(["waiting", "offered"])
            )
            .first()
        )

        if existing:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Already on the waitlist"}
            )

        entry = WaitlistEntry(
            user_id=user_id,
            event_id=event_id,
            quantity=quantity,
            status="waiting"
        )

        db.add(entry)
        db.flush()

        return self.reply(
            db, message, "AGREE",
            {
                "waitlist_id": entry.id,
                "event_id": event_id,
                "quantity": quantity,
                "status": "waiting"
            }
        )

    def reply(self, db, original, performative, content):
        return send_message(
            db=db,
            sender="WaitlistAgent",
            receiver=original.sender,
            performative=performative,
            content=content,
            conversation_id=original.conversation_id
        )


    def process_available_tickets(self, db, message, content):
        event_id = content.get("event_id")

        event = db.get(Event, event_id)

        if event is None:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Event not found"}
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if event.status != "published" or event.start_time <= now:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Event is not available"}
            )

        available = event.ticket_quantity - event.reserved_quantity

        if available <= 0:
            return self.reply(
                db, message, "INFORM",
                {"offers_created": 0, "reason": "No tickets available"}
            )

        waiting_entries = (
            db.query(WaitlistEntry)
            .filter(
                WaitlistEntry.event_id == event_id,
                WaitlistEntry.status == "waiting"
            )
            .order_by(
                WaitlistEntry.created_at.asc(),
                WaitlistEntry.id.asc()
            )
            .all()
        )

        offers_created = 0

        for entry in waiting_entries:
            if entry.quantity > available:
                continue

            # Reserve inventory before issuing the offer.
            result = db.execute(
                update(Event)
                .where(
                    Event.id == event_id,
                    Event.reserved_quantity + entry.quantity
                    <= Event.ticket_quantity
                )
                .values(
                    reserved_quantity=Event.reserved_quantity + entry.quantity
                )
                .execution_options(synchronize_session=False)
            )

            if result.rowcount != 1:
                break

            entry.status = "offered"
            entry.offer_expires_at = now + timedelta(minutes=15)



            from app.agents.dispatcher import dispatch_message

            notification_request = send_message(
                db=db,
                sender="WaitlistAgent",
                receiver="NotificationAgent",
                performative="INFORM",
                content={
                    "action": "waitlist_offer",
                    "user_id": entry.user_id,
                    "event_id": entry.event_id,
                    "waitlist_id": entry.id
                },
                conversation_id=message.conversation_id
            )

            dispatch_message(db, notification_request)


            available -= entry.quantity
            offers_created += 1

        return self.reply(
            db, message, "INFORM",
            {
                "event_id": event_id,
                "offers_created": offers_created
            }
        )



    def expire_offers(self, db, message):

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        expired_entries = (
            db.query(WaitlistEntry)
            .filter(
                WaitlistEntry.status == "offered",
                WaitlistEntry.offer_expires_at <= now
            )
            .order_by(WaitlistEntry.id)
            .all()
        )

        expired_count = 0

        for entry in expired_entries:
            # Claim the offer before releasing its reservation.
            claimed = db.execute(
                update(WaitlistEntry)
                .where(
                    WaitlistEntry.id == entry.id,
                    WaitlistEntry.status == "offered",
                    WaitlistEntry.offer_expires_at <= now
                )
                .values(status="expired")
                .execution_options(synchronize_session=False)
            )

            if claimed.rowcount != 1:
                continue

            released = db.execute(
                update(Event)
                .where(
                    Event.id == entry.event_id,
                    Event.reserved_quantity >= entry.quantity
                )
                .values(
                    reserved_quantity=Event.reserved_quantity - entry.quantity
                )
            )

            if released.rowcount != 1:
                db.rollback()
                return self.reply(
                    db, message, "FAILURE",
                    {"reason": "Could not release offer inventory"}
                )

            from app.agents.dispatcher import dispatch_message

            notification_request = send_message(
                db=db,
                sender="WaitlistAgent",
                receiver="NotificationAgent",
                performative="INFORM",
                content={
                    "action": "offer_expired",
                    "user_id": entry.user_id,
                    "event_id": entry.event_id,
                    "waitlist_id": entry.id
                },
                conversation_id=message.conversation_id
            )

            dispatch_message(db, notification_request)
    

            expired_count += 1

        return self.reply(
            db, message, "INFORM",
            {"expired_offers": expired_count}
        )
