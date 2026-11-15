
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.csrf import verify_csrf
from app.database import get_db
from app.models import User, Venue
from app.schemas import VenueCreate, VenueResponse
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/venues", tags=["Venues"])


@router.get("/", response_model=list[VenueResponse])
def list_venues(db: Session = Depends(get_db)):
    return db.query(Venue).order_by(Venue.id).all()


@router.post(
    "/",
    response_model=VenueResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)]
)
def create_venue(
    venue_data: VenueCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    venue = Venue(**venue_data.model_dump())

    db.add(venue)
    db.commit()
    db.refresh(venue)

    return venue



@router.put(
    "/{venue_id}",
    response_model=VenueResponse,
    dependencies=[Depends(verify_csrf)]
)
def update_venue(
    venue_id: int,
    venue_data: VenueCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    venue = db.get(Venue, venue_id)

    if venue is None:
        raise HTTPException(
            status_code=404,
            detail="Venue not found"
        )

    for field, value in venue_data.model_dump().items():
        setattr(venue, field, value)

    db.commit()
    db.refresh(venue)

    return venue


@router.delete(
    "/{venue_id}",
    dependencies=[Depends(verify_csrf)]
)
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    venue = db.get(Venue, venue_id)

    if venue is None:
        raise HTTPException(
            status_code=404,
            detail="Venue not found"
        )

    if venue.events:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a venue with associated events"
        )

    db.delete(venue)
    db.commit()

    return {"message": "Venue deleted successfully"}



def test_unauthenticated_profile(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_unauthenticated_admin_stats(client):
    response = client.get("/admin/stats")
    assert response.status_code == 401


def test_unauthenticated_agent_logs(client):
    response = client.get("/admin/agent-logs")
    assert response.status_code == 401


def test_unauthenticated_recent_bookings(client):
    response = client.get("/admin/recent-bookings")
    assert response.status_code == 401


def test_unauthenticated_tickets(client):
    response = client.get("/tickets/my")
    assert response.status_code == 401


def test_unauthenticated_waitlist(client):
    response = client.get("/waitlist/my")
    assert response.status_code == 401


def test_unauthenticated_notifications(client):
    response = client.get("/notifications/my")
    assert response.status_code == 401


def test_unauthenticated_private_hires(client):
    response = client.get("/private-hires/my")
    assert response.status_code == 401


def test_unauthenticated_checkin(client):
    response = client.post(
        "/checkin/",
        json={
            "event_id": 1,
            "qr_token": "invalid-test-token"
        }
    )
    assert response.status_code == 401


def test_unauthenticated_booking(client):
    response = client.post(
        "/bookings/",
        json={
            "event_id": 1,
            "quantity": 1
        }
    )
    assert response.status_code == 401