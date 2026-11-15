
import json
import uuid
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.agents.booking_agent import send_message
from app.agents.dispatcher import dispatch_message
from app.models import Venue

db = SessionLocal()

try:
    venue = db.query(Venue).first()

    if venue is None:
        raise ValueError("Create a venue before running this test")

    start = datetime.now(timezone.utc) + timedelta(days=7)
    end = start + timedelta(hours=2)

    request = send_message(
        db=db,
        sender="System",
        receiver="VenueAgent",
        performative="REQUEST",
        content={
            "action": "check_event_slot",
            "venue_id": venue.id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat()
        },
        conversation_id=str(uuid.uuid4())
    )

    reply = dispatch_message(db, request)

    db.commit()

    print("VenueAgent performative:", reply.performative)
    print(json.dumps(json.loads(reply.content), indent=2))

finally:
    db.close()
