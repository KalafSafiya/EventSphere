
import json
import logging
import uuid

from apscheduler.schedulers.background import BackgroundScheduler

from app.agents.booking_agent import send_message
from app.agents.dispatcher import dispatch_message
from app.database import SessionLocal

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def expire_waitlist_offers():
    db = SessionLocal()

    try:
        request = send_message(
            db=db,
            sender="Scheduler",
            receiver="WaitlistAgent",
            performative="REQUEST",
            content={"action": "expire_offers"},
            conversation_id=str(uuid.uuid4())
        )

        reply = dispatch_message(db, request)

        if reply.performative == "FAILURE":
            db.rollback()
            logger.error("Waitlist expiration failed: %s", reply.content)
            return

        db.commit()

        result = json.loads(reply.content)

        if result.get("expired_offers", 0) > 0:
            logger.info("Expired offers: %s", result["expired_offers"])

    except Exception:
        db.rollback()
        logger.exception("Waitlist expiration job failed")

    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            expire_waitlist_offers,
            trigger="interval",
            minutes=1,
            id="expire_waitlist_offers",
            replace_existing=True,
            max_instances=1
        )
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
