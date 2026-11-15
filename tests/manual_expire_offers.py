
import json
import uuid

from app.database import SessionLocal
from app.agents.booking_agent import send_message
from app.agents.waitlist_agent import WaitlistAgent

db = SessionLocal()

try:
    request = send_message(
        db=db,
        sender="System",
        receiver="WaitlistAgent",
        performative="REQUEST",
        content={"action": "expire_offers"},
        conversation_id=str(uuid.uuid4())
    )

    reply = WaitlistAgent().handle_message(db, request)

    db.commit()

    print(json.dumps(json.loads(reply.content), indent=2))

finally:
    db.close()
