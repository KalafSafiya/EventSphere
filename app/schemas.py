
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Literal["admin", "staff", "attendee"]

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MessageResponse(BaseModel):
    message: str


class VenueCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    location: str = Field(min_length=2, max_length=255)
    capacity: int = Field(gt=0)
    description: str | None = None
    image_url: str | None = None
    hourly_rate: float = Field(ge=0)
    private_hire_enabled: bool = False


class VenueResponse(VenueCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)



from datetime import datetime
from pydantic import model_validator


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    category: str = Field(min_length=2, max_length=100)
    start_time: datetime
    end_time: datetime
    ticket_price: float = Field(ge=0)
    ticket_quantity: int = Field(gt=0)
    venue_id: int

    @model_validator(mode="after")
    def validate_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("End time must be after start time")
        return self


class EventResponse(EventCreate):
    id: int
    organizer_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)



class BookingCreate(BaseModel):
    event_id: int
    quantity: int = Field(gt=0, le=10)


class BookingResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    quantity: int
    total_amount: float
    status: str

    model_config = ConfigDict(from_attributes=True)



class PaymentRequest(BaseModel):
    success: bool


class PaymentResponse(BaseModel):
    booking_id: int
    amount: float
    status: str
    transaction_reference: str | None = None


class CheckInRequest(BaseModel):
    qr_token: str = Field(min_length=10)
    event_id: int = Field(gt=0)



class WaitlistCreate(BaseModel):
    event_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=10)


class WaitlistResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    quantity: int
    status: str
    offer_expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

