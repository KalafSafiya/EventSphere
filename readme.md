# EventSphere

### Multi-Agent Event Management System

**Module:** IT4123 – Agent Based Computing (ICA 02)   
**Developed by:** Safiya Kalaf  
**Registration Number:** 2021/ICT/71

## About the Project

EventSphere is a web-based event management system developed as part of my Agent Based Computing assignment.

The main purpose of this project is to demonstrate how multiple software agents can communicate and work together to manage different tasks in an event management system.

EventSphere allows users to explore events, book tickets, make simulated payments, receive QR tickets, and join waitlists when events are fully booked. It also supports private venue bookings, event administration, and ticket check-in by authorized staff members.

Instead of handling every operation through a single component, I developed five agents with different responsibilities. These agents communicate through a message dispatcher to complete tasks such as reserving tickets, checking venue availability, issuing tickets, managing waitlists, and generating notifications.

For example, when a user cancels a booking, the reserved tickets become available again. The WaitlistAgent checks whether another user is waiting for tickets and, if possible, creates an offer. The NotificationAgent then notifies that user about the available tickets.

This interaction between agents is one of the main features of EventSphere.

## Live Application

EventSphere is deployed on an AWS EC2 instance and can be accessed through the following HTTPS address:

**Live URL:** https://eventsphere-safiya.duckdns.org

**GitHub Repository:** https://github.com/KalafSafiya/EventSphere

The deployed application supports three user roles: Admin, Gate Staff, and Attendee.

## Main Features

### Event Management

Users can browse available events, view event details, and check ticket availability.

Administrators can create, publish, and manage events through the Admin Dashboard.

### Ticket Booking and Payments

Attendees can book tickets for events and complete simulated payments.

The system checks ticket availability before confirming bookings and prevents users from booking more tickets than the available capacity.

If a booking is cancelled or a payment fails, the reserved tickets are released.

Payments are simulated for demonstration purposes. No real payment gateway or financial transaction is involved.

### QR Tickets and Check-in

After a successful booking, the system generates QR tickets for attendees.

Authorized Gate Staff can use the check-in interface to validate tickets when attendees arrive at an event.

The system prevents the same ticket from being checked in more than once.

### Waitlist Management

When an event does not have enough available tickets, users can join a waitlist.

If tickets become available through cancellations or other releases, the WaitlistAgent checks the waiting users and creates ticket offers when possible.

Each offer remains valid for 15 minutes. If the user does not accept it within that period, the offer expires and the tickets are released.

### Notifications

The system generates in-app notifications for important activities, including booking confirmations, booking cancellations, waitlist offers, and offer expiration.

### Venue Management

EventSphere allows administrators to manage venues and their availability.

Users can also request venues for private events when private hire is enabled.

The VenueAgent checks for scheduling conflicts to help prevent overlapping venue bookings.

### User Roles and Staff Management

EventSphere has three user roles:

- **Admin:** Manages events, venues, staff permissions, private-hire requests, and system information.
- **Gate Staff:** Validates attendee tickets and handles event check-in.
- **Attendee:** Browses events, books tickets, views QR tickets, receives notifications, and requests private venue bookings.

Administrators can assign the Gate Staff role to registered users and revoke that role when necessary.

Newly registered users receive the Attendee role by default.

## Agents in EventSphere

The system contains five main agents.

### 1. BookingAgent

The BookingAgent handles ticket booking requests.

It checks whether an event is available, whether the event has already started, and whether enough tickets remain.

If the booking is valid, it reserves the requested tickets and calculates the booking amount. Otherwise, it rejects the request with an appropriate reason.

### 2. TicketAgent

The TicketAgent manages QR ticket generation and validation.

It creates tickets for confirmed bookings and checks their validity during event entry.

It also prevents duplicate ticket check-ins.

### 3. WaitlistAgent

The WaitlistAgent manages users waiting for tickets.

When tickets become available, it checks the waitlist and creates offers for eligible users.

It also manages offer expiration and releases tickets when offers are not accepted within the allowed time.

### 4. NotificationAgent

The NotificationAgent creates notifications for users.

For example, when the WaitlistAgent creates a ticket offer, it communicates with the NotificationAgent to notify the waiting user.

### 5. VenueAgent

The VenueAgent manages venue availability and private-hire scheduling.

It checks whether a venue is available for the requested date and time and helps prevent overlapping reservations.

## How the Agents Communicate

The agents run within the same Python application and communicate through a message dispatcher.

Messages contain details such as the sender, receiver, message type, content, conversation ID, and timestamp.

The system uses the following message types:

| Message Type | Purpose |
|---|---|
| REQUEST | Request an action from another agent |
| AGREE | Accept a request |
| REFUSE | Reject a request |
| INFORM | Share information or an operation result |
| FAILURE | Report an unsuccessful operation |

Agent messages are stored in the database.

The Admin Dashboard also includes an agent message log, allowing the communication between agents to be viewed.

## Technologies Used

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Template Engine | Jinja2 |
| Database | SQLite |
| ORM | SQLAlchemy |
| QR Code Generation | Python qrcode |
| Background Scheduling | APScheduler |
| Testing | pytest |
| API Documentation | Swagger UI |
| Cloud Hosting | AWS EC2 |
| Server Operating System | Ubuntu |
| Application Server | Uvicorn |
| Service Management | systemd |
| Domain | DuckDNS |
| Version Control | Git and GitHub |

## How to Run EventSphere Locally

The following instructions explain how to set up and run EventSphere on a local computer.

### Step 1: Clone the Repository

Open a terminal and clone the project:

```bash
git clone https://github.com/KalafSafiya/EventSphere.git
```

Move into the project directory:

```bash
cd EventSphere
```

Switch to the development branch containing the latest application changes:

```bash
git checkout develop
```

Run the following commands from the directory containing `requirements.txt` and the `app` folder.

### Step 2: Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

On Windows, activate it using:

```cmd
.venv\Scripts\activate.bat
```

On Linux or macOS, use:

```bash
source .venv/bin/activate
```

### Step 3: Install Dependencies

Install the required Python packages:

```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

EventSphere uses environment variables for application configuration.

The main database setting is `DATABASE_URL`.

For local development, the application uses SQLite by default:

```env
DATABASE_URL=sqlite:///./eventsphere.db
```

If `DATABASE_URL` is not provided, the application uses this default SQLite connection.

Other authentication, security, or deployment-specific environment variables should be configured according to the application's environment settings.

Sensitive values such as passwords, secret keys, and production credentials should not be committed to GitHub.

### Step 5: Start the Application

Run the FastAPI application using Uvicorn:

```bash
python -m uvicorn app.main:app --reload
```

Once the server starts, open:

http://127.0.0.1:8000

The interactive API documentation is available at:

http://127.0.0.1:8000/docs

The database tables are created automatically when the application starts.

## Demo Accounts

The application supports three roles for demonstration and evaluation.

| Role | Email | Password |
|---|---|---|
| Admin | kalafsafiya2019@gmail.com  | abc@1234 |
| Gate Staff | gatestaff1@gmail.com  | 12345678 |
| Attendee | jane@gmail.com | 12345678 |

These accounts can be used to demonstrate the different functionalities available to each role.

The Admin account can access event management, venue management, and staff management features.

The Gate Staff account can access ticket check-in.

The Attendee account can register for events, book tickets, and view QR tickets.

**Before submission:** Replace the placeholders with working, dedicated demo account credentials. Do not publish personal or production administrator passwords.

## Running the Tests

EventSphere includes automated tests developed using pytest.

The tests cover important workflows and help verify that the agents and application components behave correctly.

To run the complete test suite, activate the virtual environment and execute:

```bash
python -m pytest -q
```

For more detailed test output:

```bash
python -m pytest tests -v
```

### Test Coverage

The automated tests cover areas including:

- User authentication and API security
- Ticket availability and reservations
- BookingAgent operations
- Successful and failed payments
- Duplicate payment prevention
- QR ticket validation and duplicate check-in prevention
- Booking cancellation and ticket release
- Waitlist offers and expiration
- Notification creation
- Agent communication and integration

**Latest local test result: 34 tests passed.**

The test suite helps verify the booking, ticketing, waitlist, notification, and related application workflows.

## Deployment

EventSphere is deployed on an AWS EC2 instance running Ubuntu.

The FastAPI application runs using Uvicorn and is managed by a systemd service named `eventsphere.service`.

This allows the application to continue running after the SSH session is closed and to start automatically when the EC2 instance boots.

The deployed application uses a SQLite database stored on the server.

A DuckDNS domain and HTTPS are configured to provide public access to the application.

The latest application changes are maintained through Git and GitHub.

## Security

EventSphere includes several security measures to protect application functionality and user data.

These include password hashing, session-based authentication, role-based access restrictions, CSRF protection, booking ownership checks, duplicate payment prevention, and duplicate QR ticket check-in prevention.

Administrative operations are restricted to authorized users.

Gate Staff members can access ticket check-in functionality without receiving full administrator privileges.

## Limitations and Future Improvements

EventSphere was developed as an academic project to demonstrate agent-based computing in a practical web application.

Some areas could be improved in the future:

- Integrating a real payment gateway
- Adding email and push notifications
- Migrating from SQLite to PostgreSQL for better scalability
- Running agents as independent services
- Improving concurrency testing for simultaneous ticket bookings
- Expanding monitoring and automated deployment

## Conclusion

Developing EventSphere helped me understand how multiple agents can communicate and cooperate to complete tasks within a web application.

The most interesting part of the project was implementing interactions between the BookingAgent, WaitlistAgent, and NotificationAgent, especially when tickets become available after a cancellation.

I also gained practical experience in FastAPI development, database management, frontend integration, automated testing, application security, and cloud deployment.

By deploying EventSphere to AWS EC2, I was able to take the project beyond local development and make it accessible through a public HTTPS website.

---

**Developed by Safiya Kalaf**  
**Registration Number:** 2021/ICT/71  
