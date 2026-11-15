
from sqlalchemy.orm import Session

from app.models import AgentMessage

from app.agents.venue_agent import VenueAgent


def dispatch_message(db: Session, message: AgentMessage):
    # Import here to avoid circular imports.
    from app.agents.notification_agent import NotificationAgent
    from app.agents.waitlist_agent import WaitlistAgent
    from app.agents.ticket_agent import TicketAgent
    from app.agents.booking_agent import BookingAgent

    agents = {
        "BookingAgent": BookingAgent(),
        "TicketAgent": TicketAgent(),
        "WaitlistAgent": WaitlistAgent(),
        "NotificationAgent": NotificationAgent(),
        "VenueAgent": VenueAgent(),
    }

    agent = agents.get(message.receiver)

    if agent is None:
        raise ValueError(
            f"Unknown agent receiver: {message.receiver}"
        )

    return agent.handle_message(db, message)
