
import json
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.agents.booking_agent import send_message
from app.models import AgentMessage, Event, PrivateHire, Venue


class VenueAgent:
    # Cleaning/setup time required between activities.
    TURNAROUND_MINUTES = 30

    # Requests above this amount require admin approval.
    ESCALATION_PRICE = 50000

    def handle_message(self, db: Session, message: AgentMessage):
        try:
            content = json.loads(message.content)
            action = content.get("action")

            if message.performative != "REQUEST":
                return self.reply(
                    db, message, "REFUSE",
                    {"reason": "VenueAgent only accepts REQUEST messages"}
                )

            if action == "check_event_slot":
                return self.check_event_slot(db, message, content)

            if action == "request_private_hire":
                return self.request_private_hire(db, message, content)

            return self.reply(
                db, message, "REFUSE",
                {"reason": "Unsupported VenueAgent action"}
            )

        except (ValueError, TypeError, KeyError) as exc:
            return self.reply(
                db, message, "REFUSE",
                {"reason": f"Invalid request: {exc}"}
            )

    def parse_time(self, value):
        result = datetime.fromisoformat(value)

        if result.tzinfo is not None:
            result = result.astimezone(timezone.utc).replace(tzinfo=None)

        return result

    def find_conflict(
        self,
        db,
        venue_id,
        start_time,
        end_time
    ):
        buffer = timedelta(minutes=self.TURNAROUND_MINUTES)

        window_start = start_time - buffer
        window_end = end_time + buffer

        event_conflict = (
            db.query(Event)
            .filter(
                Event.venue_id == venue_id,
                Event.status.in_(["draft", "published"]),
                Event.start_time < window_end,
                Event.end_time > window_start
            )
            .first()
        )

        if event_conflict:
            return {
                "type": "event",
                "id": event_conflict.id
            }

        hire_conflict = (
            db.query(PrivateHire)
            .filter(
                PrivateHire.venue_id == venue_id,
                PrivateHire.status.in_(["confirmed", "pending"]),
                PrivateHire.start_time < window_end,
                PrivateHire.end_time > window_start
            )
            .first()
        )

        if hire_conflict:
            return {
                "type": "private_hire",
                "id": hire_conflict.id
            }

        return None

    def check_event_slot(self, db, message, content):
        venue_id = content["venue_id"]
        start_time = self.parse_time(content["start_time"])
        end_time = self.parse_time(content["end_time"])

        venue = db.get(Venue, venue_id)

        if venue is None:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Venue not found"}
            )

        if end_time <= start_time:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "End time must be after start time"}
            )

        conflict = self.find_conflict(
            db, venue_id, start_time, end_time
        )

        if conflict:
            return self.reply(
                db, message, "REFUSE",
                {
                    "reason": "Venue is unavailable during this time",
                    "conflict": conflict
                }
            )

        return self.reply(
            db, message, "AGREE",
            {
                "venue_id": venue_id,
                "available": True,
                "turnaround_minutes": self.TURNAROUND_MINUTES
            }
        )

    def suggest_alternatives(
        self,
        db,
        venue,
        start_time,
        end_time,
        guest_count
    ):
        duration = end_time - start_time
        alternatives = []

        # Try alternative time slots at the same venue.
        for hours in [2, 4, 6, 24]:
            proposed_start = start_time + timedelta(hours=hours)
            proposed_end = proposed_start + duration

            if not self.find_conflict(
                db, venue.id, proposed_start, proposed_end
            ):
                alternatives.append({
                    "venue_id": venue.id,
                    "venue_name": venue.name,
                    "start_time": proposed_start.isoformat(),
                    "end_time": proposed_end.isoformat()
                })

                if len(alternatives) >= 3:
                    return alternatives

        # Try other suitable venues.
        other_venues = (
            db.query(Venue)
            .filter(
                Venue.id != venue.id,
                Venue.private_hire_enabled == True,
                Venue.capacity >= guest_count
            )
            .all()
        )

        for other in other_venues:
            if not self.find_conflict(
                db, other.id, start_time, end_time
            ):
                alternatives.append({
                    "venue_id": other.id,
                    "venue_name": other.name,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                })

                if len(alternatives) >= 3:
                    break

        return alternatives

    def request_private_hire(self, db, message, content):
        venue_id = content["venue_id"]
        user_id = content["user_id"]
        start_time = self.parse_time(content["start_time"])
        end_time = self.parse_time(content["end_time"])
        purpose = content["purpose"]
        guest_count = content["guest_count"]

        venue = db.get(Venue, venue_id)

        if venue is None:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Venue not found"}
            )

        if not venue.private_hire_enabled:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Venue is not available for private hire"}
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if start_time <= now or end_time <= start_time:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Invalid or past booking time"}
            )

        if not isinstance(guest_count, int) or guest_count <= 0:
            return self.reply(
                db, message, "REFUSE",
                {"reason": "Guest count must be positive"}
            )

        if guest_count > venue.capacity:
            return self.reply(
                db, message, "PROPOSE",
                {
                    "reason": "Guest count exceeds venue capacity",
                    "alternatives": self.suggest_alternatives(
                        db, venue, start_time, end_time, guest_count
                    )
                }
            )

        duration_hours = (
            end_time - start_time
        ).total_seconds() / 3600

        total_price = round(
            duration_hours * venue.hourly_rate, 2
        )

        conflict = self.find_conflict(
            db, venue_id, start_time, end_time
        )

        if conflict:
            return self.reply(
                db, message, "PROPOSE",
                {
                    "reason": "Requested venue has a scheduling conflict",
                    "conflict": conflict,
                    "alternatives": self.suggest_alternatives(
                        db, venue, start_time, end_time, guest_count
                    )
                }
            )

        # High-value requests require manual approval.
        status = (
            "pending"
            if total_price > self.ESCALATION_PRICE
            else "confirmed"
        )

        hire = PrivateHire(
            user_id=user_id,
            venue_id=venue_id,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            guest_count=guest_count,
            total_price=total_price,
            status=status
        )

        db.add(hire)
        db.flush()

        return self.reply(
            db,
            message,
            "AGREE" if status == "confirmed" else "INFORM",
            {
                "private_hire_id": hire.id,
                "venue_id": venue_id,
                "total_price": total_price,
                "status": status,
                "reason": (
                    "Automatically confirmed"
                    if status == "confirmed"
                    else "Escalated for admin approval"
                )
            }
        )

    def reply(self, db, original, performative, content):
        return send_message(
            db=db,
            sender="VenueAgent",
            receiver=original.sender,
            performative=performative,
            content=content,
            conversation_id=original.conversation_id
        )
