
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app import models
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import users
from app.routers import auth
from app.routers import venues
from app.routers import events
from app.routers import bookings
from app.routers import payments
from app.routers import tickets
from app.routers import checkin
from app.routers import waitlist
from app.agents.scheduler import start_scheduler, stop_scheduler
from app.routers import notifications
from app.routers import private_hires
from app.routers import admin

from fastapi import Request
from fastapi.responses import HTMLResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    start_scheduler()

    try:
        yield
    finally:
        stop_scheduler()



app = FastAPI(
    title="EventSphere API",
    description="Multi-Agent Venue Booking and Digital Ticketing Platform",
    version="1.0.0",
    lifespan=lifespan
)

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

app.include_router(users.router)

app.include_router(auth.router)

app.include_router(venues.router)

app.include_router(events.router)

app.include_router(bookings.router)

app.include_router(payments.router)

app.include_router(tickets.router)

app.include_router(checkin.router)

app.include_router(waitlist.router)

app.include_router(notifications.router)

app.include_router(private_hires.router)

app.include_router(admin.router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/event/{event_id}", response_class=HTMLResponse)
def event_detail_page(event_id: int, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="event_detail.html",
        context={"event_id": event_id}
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@app.get("/payment/{booking_id}", response_class=HTMLResponse)
def payment_page(booking_id: int, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="payment.html",
        context={"booking_id": booking_id}
    )


@app.get("/my-tickets", response_class=HTMLResponse)
def my_tickets_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="my_tickets.html"
    )

@app.get("/staff/checkin", response_class=HTMLResponse)
def staff_checkin_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="staff_checkin.html"
    )

@app.get("/my-waitlist", response_class=HTMLResponse)
def my_waitlist_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="my_waitlist.html"
    )


@app.get("/my-notifications", response_class=HTMLResponse)
def my_notifications_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="my_notifications.html"
    )

@app.get("/private-hire", response_class=HTMLResponse)
def private_hire_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="private_hire.html"
    )


@app.get("/my-private-hires", response_class=HTMLResponse)
def my_private_hires_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="my_private_hires.html"
    )


@app.get("/admin/hires", response_class=HTMLResponse)
def admin_hires_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_hires.html"
    )

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html"
    )

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "EventSphere"
    }
