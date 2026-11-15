
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.database import SessionLocal
from app.models import Event, User, WaitlistEntry

db = SessionLocal()

try:
    event = db.get(Event, 4)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if event is None:
        raise ValueError("Event 4 does not exist")

    if event.status != "published" or event.start_time <= now:
        raise ValueError("Event 4 is not a future published event")

    attendee = (
        db.query(User)
        .filter(User.role == "attendee")
        .order_by(User.id)
        .first()
    )

    if attendee is None:
        raise ValueError("No attendee account exists")

    # Reserve exactly one available ticket.
    result = db.execute(
        update(Event)
        .where(
            Event.id == event.id,
            Event.reserved_quantity + 1 <= Event.ticket_quantity
        )
        .values(
            reserved_quantity=Event.reserved_quantity + 1
        )
        .execution_options(synchronize_session=False)
    )

    if result.rowcount != 1:
        raise ValueError("No available tickets for this test")

    entry = WaitlistEntry(
        user_id=attendee.id,
        event_id=event.id,
        quantity=1,
        status="offered",
        offer_expires_at=now - timedelta(minutes=1)
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    print("Created test waitlist entry:", entry.id)
    print("Status:", entry.status)
    print("Expires:", entry.offer_expires_at)

except Exception:
    db.rollback()
    raise

finally:
    db.close()
