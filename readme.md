# EventSphere 🎟️
### Multi-Agent Event Management System

**Module:** IT4123 – Agent Based Computing (ICA 02)  
**Name:** Safiya Kalaf  
**Registration Number:** 2021/ICT/71  
**University:** University of Vavuniya  
**Date:** 15th November 2026

---

## 1. About the Project

EventSphere is a web-based event management system that I developed for my Agent Based Computing assignment.

The main idea of this project is to use different agents to manage event-related tasks. Instead of handling everything in one place, I created separate agents for booking tickets, managing QR tickets, handling waitlists, sending notifications, and checking venue availability.

Users can browse events, book tickets, make simulated payments, get QR tickets, and join a waitlist when tickets are sold out. The system also supports private venue bookings and has an admin dashboard.

I wanted to build a system where the agents could communicate with each other and complete tasks automatically.

For example, when someone cancels a booking, the system releases those tickets. The WaitlistAgent then checks whether anyone is waiting for tickets. If there is a suitable user, the agent creates an offer and asks the NotificationAgent to notify that user.

This is one of the main examples of how agents work together in EventSphere.

## 2. Main Features

### User Management
- User registration and login
- Different user roles
- Secure authentication
- Access restrictions based on user roles

### Event Management
- View available events
- View event details
- Create and manage events
- Publish and cancel events

### Ticket Booking
- Book tickets for events
- Check ticket availability
- Calculate the total booking price
- Make simulated payments
- Cancel bookings
- Release tickets after cancellation or failed payment

### QR Tickets
- Generate QR tickets after successful booking
- View booked tickets
- Scan tickets during check-in
- Prevent the same ticket from being used twice

### Waitlist
- Join a waitlist when enough tickets are not available
- Receive ticket offers when tickets become available
- Accept ticket offers within 15 minutes
- Automatically expire unused offers
- Release tickets when an offer expires

### Notifications
- Ticket availability notifications
- Waitlist offer expiration notifications
- Booking confirmation notifications
- Booking cancellation notifications

### Venue Booking
- View venues
- Request venues for private events
- Check venue availability
- Prevent overlapping venue bookings
- Manage private-hire requests

### Admin Dashboard
- View system statistics
- View recent bookings
- Monitor agent messages
- Manage private-hire requests

## 3. Technologies Used

| Part | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Database | SQLite |
| Database ORM | SQLAlchemy |
| Templates | Jinja2 |
| QR Code | Python qrcode |
| Background Scheduler | APScheduler |
| Testing | pytest |
| API Documentation | Swagger UI |

I used FastAPI for the backend because it is easy to work with and helps organize the APIs.

For the frontend, I used HTML, CSS, JavaScript, and Bootstrap.

I used SQLite to store users, events, bookings, tickets, notifications, and agent messages.

## 4. Agents Used in the System

There are five main agents in EventSphere.

### 1. BookingAgent

The BookingAgent handles ticket booking requests.

It checks whether the event is available, whether it has started, and whether enough tickets are left.

If tickets are available, the agent reserves them and calculates the total price.

If the booking cannot be completed, it rejects the request with a reason.

### 2. TicketAgent

The TicketAgent manages QR tickets.

It creates tickets for confirmed bookings and checks them during event entry.

It also makes sure that the same ticket cannot be used more than once.

### 3. WaitlistAgent

The WaitlistAgent manages users who are waiting for tickets.

When an event does not have enough tickets, users can join the waitlist.

If someone cancels a booking, the WaitlistAgent checks the waiting users and offers the available tickets.

Each offer is valid for 15 minutes. If the user does not accept it within that time, the tickets are released.

### 4. NotificationAgent

The NotificationAgent creates notifications for users.

For example, when the WaitlistAgent creates a ticket offer, it sends a message to the NotificationAgent.

The NotificationAgent then creates a notification that the user can see in the application.

### 5. VenueAgent

The VenueAgent manages venue availability.

It checks whether a venue is already booked for a requested time.

It also helps handle private-hire requests and avoids scheduling conflicts.

## 5. How the Agents Communicate

The agents communicate by sending messages to each other.

Each message contains information such as:

- Sender
- Receiver
- Message type (performative)
- Message content
- Conversation ID
- Time

The system uses these message types:

| Message | Meaning |
|---|---|
| REQUEST | Ask an agent to do something |
| AGREE | Accept a request |
| REFUSE | Reject a request |
| INFORM | Share information or a result |
| FAILURE | Report that an operation failed |

All agent messages are stored in the database.

I also added an agent message log in the admin dashboard so the communication between agents can be viewed.

The agents run inside the same Python application and use a dispatcher to send messages to the correct agent.

## 6. Example of Agents Working Together

One example is when a user cancels a ticket booking.

1. The user cancels the booking.
2. The system releases the reserved tickets.
3. A message is sent to the WaitlistAgent.
4. The WaitlistAgent checks whether anyone is waiting for tickets.
5. If tickets can be offered, the agent creates a 15-minute offer.
6. The WaitlistAgent sends a message to the NotificationAgent.
7. The NotificationAgent creates a notification for the waiting user.
8. If the offer expires, the tickets are released again.

This workflow shows how two agents can communicate and complete a task together.

## 7. Project Structure

```text
backend/
│
├── app/
│   ├── agents/
│   │   ├── booking_agent.py
│   │   ├── ticket_agent.py
│   │   ├── waitlist_agent.py
│   │   ├── notification_agent.py
│   │   ├── venue_agent.py
│   │   ├── dispatcher.py
│   │   └── scheduler.py
│   │
│   ├── routers/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── bookings.py
│   │   ├── checkin.py
│   │   ├── events.py
│   │   ├── notifications.py
│   │   ├── payments.py
│   │   ├── private_hires.py
│   │   ├── tickets.py
│   │   ├── users.py
│   │   ├── venues.py
│   │   └── waitlist.py
│   │
│   ├── templates/
│   ├── static/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── schemas.py
│   ├── auth.py
│   ├── csrf.py
│   └── security.py
│
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_api_security.py
│   ├── test_booking_agent.py
│   ├── test_payment.py
│   ├── test_ticket_checkin.py
│   └── test_waitlist_integration.py
│
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md
```

## 8. How to Run the Project

**Step 1:** Open the backend folder in your terminal.

```cmd
cd eventsphere\backend
```

**Step 2:** Create a virtual environment.

```cmd
python -m venv .venv
```

**Step 3:** Activate the virtual environment.

```cmd
.venv\Scripts\activate.bat
```

**Step 4:** Install the required packages.

```cmd
python -m pip install -r requirements.txt
```

**Step 5:** Start the server.

```cmd
python -m uvicorn app.main:app --reload
```

**Step 6:** Open the application in your browser.

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

The database tables are created automatically when the application starts.

## 9. Testing

I tested the main features of EventSphere using pytest.

The tests include:

- User authentication and API security
- BookingAgent ticket reservations
- Checking ticket availability
- Successful and failed payments
- Preventing duplicate payments
- QR ticket check-in
- Booking cancellation
- Waitlist ticket offers
- Expired waitlist offers
- Notification creation
- Communication between agents

To run the tests:

```cmd
python -m pytest tests -v
```

**Test Result: 34 tests passed.**

I also tested the application manually through the browser to check registration, login, booking, payments, tickets, waitlists, notifications, and private-hire requests.

## 10. Security

I added some security features to the system, including:

- Password hashing
- Login sessions
- Role-based access
- CSRF protection
- Checking booking ownership
- Preventing duplicate payments
- Preventing QR tickets from being used twice

Payments are simulated, so no real money is involved.

## 11. Challenges I Faced

While developing EventSphere, I faced a few challenges.

**Ticket availability:** I had to make sure that tickets were reserved and released correctly. For example, when a payment fails, the reserved tickets should become available again.

**Agent communication:** Connecting the agents was another challenge. I had to make sure that one agent could send a message to another agent and that the correct action would happen.

**Waitlist handling:** I had to manage ticket offers that expire after 15 minutes and make sure those tickets are released correctly.

**Testing:** Some tests failed because of changes I made during development. I fixed those issues and added more tests to check the main workflows.

**Frontend integration:** I also spent time connecting the frontend pages to the backend APIs and checking that the features worked correctly in the browser.

## 12. Limitations

There are still some things that could be improved in the future.

- Add a real payment gateway
- Send email or push notifications
- Use a production database
- Run agents as separate services
- Improve testing for multiple users booking at the same time

For now, EventSphere is designed as a working academic project that demonstrates agent-based computing.

## 13. Conclusion

Through this project, I learned how different agents can work together to complete tasks.

The most interesting part was connecting the BookingAgent, WaitlistAgent, and NotificationAgent. When a booking is cancelled, the system can automatically release tickets, offer them to waiting users, and create notifications.

I also gained more experience with FastAPI, databases, frontend development, and automated testing.

EventSphere helped me understand how agent-based computing can be used in a real web application.

---

**Developed by Safiya Kalaf**  
**Registration Number: 2021/ICT/71**  
**University of Vavuniya**  
**IT4123 – Agent Based Computing (ICA 02)**