
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.agents.ticket_agent import TicketAgent
from app.auth import require_staff
from app.csrf import verify_csrf
from app.database import get_db
from app.models import User
from app.schemas import CheckInRequest

router = APIRouter(prefix="/checkin", tags=["Check-in"])


@router.post("/", dependencies=[Depends(verify_csrf)])
def check_in_ticket(
    data: CheckInRequest,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff)
):
    request_message = send_message(
        db=db,
        sender=f"Staff:{staff.id}",
        receiver="TicketAgent",
        performative="REQUEST",
        content={
            "action": "check_in",
            "qr_token": data.qr_token,
            "event_id": data.event_id
        },
        conversation_id=str(uuid.uuid4())
    )

    reply = TicketAgent().handle_checkin(db, request_message)
    result = json.loads(reply.content)

    db.commit()

    if reply.performative == "REFUSE":
        raise HTTPException(status_code=409, detail=result)

    return {
        "message": "Check-in successful",
        **result
    }
