
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from app.database import Base

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="attendee")
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    organized_events = relationship("Event", back_populates="organizer")


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    hourly_rate = Column(Float, nullable=False, default=0.0)
    private_hire_enabled = Column(Boolean, default=False)

    events = relationship("Event", back_populates="venue")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    ticket_price = Column(Float, nullable=False, default=0.0)
    ticket_quantity = Column(Integer, nullable=False)
    reserved_quantity = Column(Integer, nullable=False, default=0)

    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    venue = relationship("Venue", back_populates="events")
    organizer = relationship("User", back_populates="organized_events")



class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User")
    event = relationship("Event")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False,
        unique=True
    )

    amount = Column(Float, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )

    transaction_reference = Column(
        String(100),
        unique=True,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    booking = relationship("Booking")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(100), nullable=False, index=True)
    sender = Column(String(100), nullable=False)
    receiver = Column(String(100), nullable=False)
    performative = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )



class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )
    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False
    )
    qr_token = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    status = Column(
        String(20),
        nullable=False,
        default="valid"
    )
    checked_in_at = Column(DateTime, nullable=True)

    booking = relationship("Booking")
    event = relationship("Event")



class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="waiting"
    )

    offer_expires_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User")
    event = relationship("Event")



class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    notification_type = Column(
        String(50),
        nullable=False,
        default="general"
    )

    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User")



class PrivateHire(Base):
    __tablename__ = "private_hires"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    venue_id = Column(
        Integer,
        ForeignKey("venues.id"),
        nullable=False
    )

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    purpose = Column(String(255), nullable=False)
    guest_count = Column(Integer, nullable=False)

    total_price = Column(Float, nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="pending"
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

