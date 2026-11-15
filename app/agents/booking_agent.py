
import json
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import AgentMessage, Event


def send_message(
    db: Session,
    sender: str,
    receiver: str,
    performative: str,
    content: dict,
    conversation_id: str
):
    message = AgentMessage(
        sender=sender,
        receiver=receiver,
        performative=performative,
        content=json.dumps(content),
        conversation_id=conversation_id
    )
    db.add(message)
    db.flush()
    return message


class BookingAgent:

    def handle_message(self, db: Session, message: AgentMessage):
        content = json.loads(message.content)

        if message.performative != "REQUEST":
            return self.reply(db, message, "REFUSE", {
                "reason": "Unsupported performative"
            })

        if content.get("action") != "reserve_tickets":
            return self.reply(db, message, "REFUSE", {
                "reason": "Unsupported action"
            })

        event_id = content["event_id"]
        quantity = content["quantity"]

        event = db.get(Event, event_id)

        if event is None:
            return self.reply(db, message, "REFUSE", {
                "reason": "Event not found"
            })

        if event.status != "published":
            return self.reply(db, message, "REFUSE", {
                "reason": "Event is not published"
            })

        if event.start_time <= datetime.now(timezone.utc).replace(tzinfo=None):
            return self.reply(db, message, "REFUSE", {
                "reason": "Event has already started"
            })

        if quantity <= 0:
            return self.reply(db, message, "REFUSE", {
                "reason": "Invalid quantity"
            })

        # Conditional SQL UPDATE reserves inventory atomically.
        result = db.execute(
            update(Event)
            .where(
                Event.id == event_id,
                Event.status == "published",
                Event.reserved_quantity + quantity <= Event.ticket_quantity
            )
            .values(
                reserved_quantity=Event.reserved_quantity + quantity
            )
            .execution_options(synchronize_session=False)
        )

        if result.rowcount != 1:
            return self.reply(db, message, "REFUSE", {
                "reason": "Not enough tickets available"
            })

        return self.reply(db, message, "AGREE", {
            "event_id": event_id,
            "quantity": quantity,
            "total_amount": round(event.ticket_price * quantity, 2)
        })

    def reply(self, db, original, performative, content):
        return send_message(
            db,
            "BookingAgent",
            original.sender,
            performative,
            content,
            original.conversation_id
        )
