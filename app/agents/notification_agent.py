
import json

from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.models import AgentMessage, Notification, User


class NotificationAgent:

    def handle_message(
        self,
        db: Session,
        message: AgentMessage
    ):
        content = json.loads(message.content)

        if message.performative != "INFORM":
            return self.reply(
                db, message, "REFUSE",
                {"reason": "NotificationAgent expects INFORM messages"}
            )

        action = content.get("action")
        user_id = content.get("user_id")

        user = db.get(User, user_id) if isinstance(user_id, int) else None

        if user is None:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Notification recipient not found"}
            )

        templates = {
            "waitlist_offer": (
                "Tickets Available!",
                "Tickets are available for your waitlisted event. "
                "Accept your offer within 15 minutes."
            ),
            "offer_expired": (
                "Waitlist Offer Expired",
                "Your ticket offer expired because it was not accepted."
            ),
            "booking_confirmed": (
                "Booking Confirmed!",
                "Your payment was successful and your booking is confirmed."
            ),
            "booking_cancelled": (
                "Booking Cancelled",
                "Your booking has been cancelled."
            )
        }

        if action not in templates:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Unsupported notification action"}
            )

        title, notification_message = templates[action]

        notification = Notification(
            user_id=user_id,
            title=title,
            message=notification_message,
            notification_type=action
        )

        db.add(notification)
        db.flush()

        return self.reply(
            db, message, "INFORM",
            {
                "notification_id": notification.id,
                "user_id": user_id,
                "action": action,
                "status": "created"
            }
        )

    def reply(self, db, original, performative, content):
        return send_message(
            db=db,
            sender="NotificationAgent",
            receiver=original.sender,
            performative=performative,
            content=content,
            conversation_id=original.conversation_id
        )
