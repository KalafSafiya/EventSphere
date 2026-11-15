
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.agents.dispatcher import dispatch_message
from app.auth import require_admin
from app.csrf import verify_csrf
from app.database import get_db
from app.models import Event, User, Venue
from app.schemas import EventCreate, EventResponse


router = APIRouter(prefix="/events", tags=["Events"])


# --------------------------------------------------
# GET ALL EVENTS
# --------------------------------------------------

@router.get("/", response_model=list[EventResponse])
def list_events(
    category: str | None = None,
    event_status: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)

    if category:
        query = query.filter(Event.category == category)

    if event_status:
        query = query.filter(Event.status == event_status)

    return query.order_by(Event.start_time).all()


# --------------------------------------------------
# GET EVENT BY ID
# --------------------------------------------------

@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event


# --------------------------------------------------
# CREATE EVENT - VENUE AGENT INTEGRATION
# --------------------------------------------------

@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)]
)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    # 1. Check whether the venue exists.
    venue = db.get(Venue, event_data.venue_id)

    if venue is None:
        raise HTTPException(
            status_code=404,
            detail="Venue not found"
        )

    # 2. Validate venue capacity.
    if event_data.ticket_quantity > venue.capacity:
        raise HTTPException(
            status_code=400,
            detail="Ticket quantity exceeds venue capacity"
        )

    # 3. Normalize datetimes to naive UTC.
    start = event_data.start_time
    end = event_data.end_time

    if start.tzinfo is not None:
        start = start.astimezone(timezone.utc).replace(tzinfo=None)

    if end.tzinfo is not None:
        end = end.astimezone(timezone.utc).replace(tzinfo=None)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if start <= now:
        raise HTTPException(
            status_code=400,
            detail="Event must start in the future"
        )

    if end <= start:
        raise HTTPException(
            status_code=400,
            detail="Event end time must be after start time"
        )

    # 4. Send a REQUEST message to VenueAgent.
    conversation_id = str(uuid.uuid4())

    request_message = send_message(
        db=db,
        sender="EventAPI",
        receiver="VenueAgent",
        performative="REQUEST",
        content={
            "action": "check_event_slot",
            "venue_id": event_data.venue_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat()
        },
        conversation_id=conversation_id
    )

    # 5. Dispatcher routes the message to VenueAgent.
    reply_message = dispatch_message(db, request_message)

    # 6. Read VenueAgent's decision.
    result = json.loads(reply_message.content)

    if reply_message.performative != "AGREE":
        # Keep the agent conversation in the database
        # even though event creation was rejected.
        db.commit()

        raise HTTPException(
            status_code=409,
            detail={
                "message": "VenueAgent rejected the requested slot",
                "agent_decision": reply_message.performative,
                "agent_response": result,
                "conversation_id": conversation_id
            }
        )

    # 7. VenueAgent approved the requested slot.
    event_values = event_data.model_dump()
    event_values["start_time"] = start
    event_values["end_time"] = end

    event = Event(
        **event_values,
        organizer_id=admin.id,
        status="draft"
    )

    db.add(event)

    # Save the event and agent messages together.
    db.commit()
    db.refresh(event)

    return event


# --------------------------------------------------
# PUBLISH EVENT
# --------------------------------------------------

@router.post(
    "/{event_id}/publish",
    response_model=EventResponse,
    dependencies=[Depends(verify_csrf)]
)
def publish_event(
    event_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if event.status != "draft":
        raise HTTPException(
            status_code=409,
            detail="Only draft events can be published"
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if event.start_time <= now:
        raise HTTPException(
            status_code=400,
            detail="Cannot publish an event that has already started"
        )

    event.status = "published"

    db.commit()
    db.refresh(event)

    return event


# --------------------------------------------------
# CANCEL EVENT
# --------------------------------------------------

@router.post(
    "/{event_id}/cancel",
    response_model=EventResponse,
    dependencies=[Depends(verify_csrf)]
)
def cancel_event(
    event_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if event.status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail="Event is already cancelled"
        )

    event.status = "cancelled"

    db.commit()
    db.refresh(event)

    return event
