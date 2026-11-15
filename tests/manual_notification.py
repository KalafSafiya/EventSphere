
import json
import uuid

from app.database import SessionLocal
from app.agents.booking_agent import send_message
from app.agents.dispatcher import dispatch_message

db = SessionLocal()

try:
    message = send_message(
        db=db,
        sender="System",
        receiver="NotificationAgent",
        performative="INFORM",
        content={
            "action": "booking_confirmed",
            "user_id": 1
        },
        conversation_id=str(uuid.uuid4())
    )

    reply = dispatch_message(db, message)

    if reply.performative != "INFORM":
        db.rollback()
        print("Notification failed:", reply.content)
    else:
        db.commit()
        print("NotificationAgent response:")
        print(json.dumps(json.loads(reply.content), indent=2))

finally:
    db.close()
