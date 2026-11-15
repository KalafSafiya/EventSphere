
document.addEventListener("DOMContentLoaded", loadEvents);

async function loadEvents() {
    const container = document.getElementById("eventsContainer");

    if (!container) return;

    try {
        const response = await fetch("/events/?event_status=published");

        if (!response.ok) {
            throw new Error("Failed to load events");
        }

        const events = await response.json();

        container.innerHTML = "";

        if (events.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <p class="text-muted">
                        No upcoming events available.
                    </p>
                </div>
            `;
            return;
        }

        events.forEach(event => {
            const card = document.createElement("div");
            card.className = "col-md-6 col-lg-4";

            const title = document.createElement("h5");
            title.className = "card-title fw-bold";
            title.textContent = event.title;

            const category = document.createElement("span");
            category.className = "badge bg-primary event-category";
            category.textContent = event.category;

            const description = document.createElement("p");
            description.className = "card-text text-muted mt-3";
            description.textContent = event.description || "";

            const date = document.createElement("p");
            date.className = "small text-secondary";
            date.textContent =
                "Date: " + new Date(event.start_time).toLocaleString();

            const price = document.createElement("p");
            price.className = "fw-semibold";
            price.textContent =
                "Ticket Price: LKR " + Number(event.ticket_price).toFixed(2);

            const button = document.createElement("a");
            button.className = "btn btn-primary w-100";
            button.href = `/event/${event.id}`;
            button.textContent = "View Event";

            const body = document.createElement("div");
            body.className = "card-body";

            body.append(category, title, description, date, price, button);

            const wrapper = document.createElement("div");
            wrapper.className = "card event-card h-100 shadow-sm";
            wrapper.appendChild(body);

            card.appendChild(wrapper);
            container.appendChild(card);
        });

    } catch (error) {
        console.error(error);

        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    Unable to load events. Please try again.
                </div>
            </div>
        `;
    }
}


document.addEventListener("DOMContentLoaded", loadEventDetail);

async function loadEventDetail() {
    const container = document.getElementById("eventDetail");

    if (!container) return;

    const eventId = window.location.pathname.split("/").pop();

    try {
        const response = await fetch(`/events/${eventId}`);

        if (!response.ok) {
            throw new Error("Event not found");
        }

        const event = await response.json();

        container.innerHTML = `
            <div class="col-lg-8">
                <div class="card shadow-sm border-0 rounded-4">
                    <div class="card-body p-4 p-md-5">
                        <span class="badge bg-primary mb-3"
                              id="detailCategory"></span>

                        <h1 class="fw-bold" id="detailTitle"></h1>

                        <p class="text-muted mt-3"
                           id="detailDescription"></p>

                        <hr>

                        <p><strong>Date:</strong>
                            <span id="detailDate"></span>
                        </p>

                        <p><strong>Venue ID:</strong>
                            <span id="detailVenue"></span>
                        </p>

                        <p><strong>Price:</strong>
                            LKR <span id="detailPrice"></span>
                        </p>

                        <p><strong>Available Tickets:</strong>
                            <span id="detailAvailable"></span>
                        </p>

                        <hr>

                        <form id="bookingForm">
                            <label for="ticketQuantity"
                                   class="form-label fw-semibold">
                                Number of Tickets
                            </label>

                            <input
                                type="number"
                                id="ticketQuantity"
                                class="form-control mb-3"
                                min="1"
                                value="1"
                                required
                            >

                            <button
                                type="submit"
                                class="btn btn-primary btn-lg w-100"
                                id="bookButton"
                            >
                                Book Tickets
                            </button>
                        </form>

                        <div id="bookingMessage" class="mt-3"></div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById("detailCategory").textContent =
            event.category;

        document.getElementById("detailTitle").textContent =
            event.title;

        document.getElementById("detailDescription").textContent =
            event.description || "";

        document.getElementById("detailDate").textContent =
            new Date(event.start_time).toLocaleString();

        document.getElementById("detailVenue").textContent =
            event.venue_id;

        document.getElementById("detailPrice").textContent =
            Number(event.ticket_price).toFixed(2);

        // Availability is an estimate until the booking API
        // atomically reserves the requested tickets.
        const available = Math.max(
            0,
            event.ticket_quantity - (event.reserved_quantity ?? 0)
        );

        document.getElementById("detailAvailable").textContent =
            available;

        const quantityInput = document.getElementById("ticketQuantity");
        const bookButton = document.getElementById("bookButton");


        const waitlistButton = document.createElement("button");
        waitlistButton.type = "button";
        waitlistButton.className = "btn btn-outline-primary w-100 mt-3";
        waitlistButton.textContent = "Join Waitlist";

        document.getElementById("bookingForm").appendChild(waitlistButton);

        waitlistButton.addEventListener("click", async () => {
            const quantity = Number(quantityInput.value);
            const message = document.getElementById("bookingMessage");

            if (!Number.isInteger(quantity) || quantity < 1 || quantity > 10) {
                message.textContent = "Choose between 1 and 10 tickets.";
                return;
            }

            waitlistButton.disabled = true;
            message.textContent = "Joining waitlist...";

            try {
                const response = await fetch("/waitlist/", {
                    method: "POST",
                    credentials: "same-origin",
                    headers: csrfHeaders(true),
                    body: JSON.stringify({
                        event_id: event.id,
                        quantity: quantity
                    })
                });

                if (response.status === 401) {
                    window.location.assign(
                        "/login?next=" +
                        encodeURIComponent(window.location.pathname)
                    );
                    return;
                }

                await readApiResponse(response);

                window.location.assign("/my-waitlist");

            } catch (error) {
                message.className = "alert alert-danger mt-3";
                message.textContent = error.message;
                waitlistButton.disabled = false;
            }
        });


        quantityInput.max = Math.min(available, 10);

        if (event.status !== "published" || available === 0) {
            quantityInput.disabled = true;
            bookButton.disabled = true;
            bookButton.textContent = "Booking Unavailable";
        }

        document.getElementById("bookingForm").addEventListener(
            "submit",
            async (e) => {
                e.preventDefault();

                const quantity = Number(quantityInput.value);
                const message = document.getElementById("bookingMessage");

                if (
                    !Number.isInteger(quantity) ||
                    quantity < 1 ||
                    quantity > available
                ) {
                    message.textContent = "Please select a valid ticket quantity.";
                    return;
                }

                bookButton.disabled = true;
                message.textContent = "Creating your booking...";

                try {
                    const csrfToken = getCookie("eventsphere_csrf");

                    const bookingResponse = await fetch("/bookings/", {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRF-Token": csrfToken || ""
                        },
                        body: JSON.stringify({
                            event_id: event.id,
                            quantity: quantity
                        })
                    });

                    if (bookingResponse.status === 401) {
                        window.location.assign(
                            "/login?next=" +
                            encodeURIComponent(window.location.pathname)
                        );
                        return;
                    }

                    const result = await bookingResponse.json();

                    if (!bookingResponse.ok) {
                        throw new Error(
                            typeof result.detail === "string"
                                ? result.detail
                                : JSON.stringify(result.detail || "Booking failed")
                        );
                    }

                    message.className = "alert alert-success mt-3";
                    message.textContent =
                        `Booking #${result.id} created! Redirecting to payment...`;

                    window.location.assign(`/payment/${result.id}`);

                } catch (error) {
                    message.className = "alert alert-danger mt-3";
                    message.textContent = error.message;
                    bookButton.disabled = false;
                }
            }
        );

    } catch (error) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    Unable to load event details.
                </div>
            </div>
        `;
    }
}

function getCookie(name) {
    const cookies = document.cookie.split(";");

    for (const cookie of cookies) {
        const [key, ...value] = cookie.trim().split("=");

        if (key === name) {
            return decodeURIComponent(value.join("="));
        }
    }

    return null;
}


document.addEventListener("DOMContentLoaded", () => {
    initializeAuthentication();
    setupLoginForm();
    setupRegistrationForm();
    setupLogout();
});

async function initializeAuthentication() {
    try {
        const response = await fetch("/auth/me", {
            credentials: "same-origin"
        });

        if (!response.ok) return;

        const user = await response.json();


        document.getElementById("loginNav")?.classList.add("d-none");
        document.getElementById("registerNav")?.classList.add("d-none");

        document.getElementById("userNav")?.classList.remove("d-none");
        document.getElementById("logoutNav")?.classList.remove("d-none");

        const managementNav = document.getElementById("managementNav");

        if (user.role === "admin" || user.role === "staff") {
            managementNav?.classList.remove("d-none");

            document.getElementById("staffCheckinNav")
                ?.classList.remove("d-none");
        }

        if (user.role === "admin") {
            document.getElementById("adminDashboardNav")
                ?.classList.remove("d-none");

            document.getElementById("adminHiresNav")
                ?.classList.remove("d-none");
        }

        const nameElement = document.getElementById("currentUserName");

        if (nameElement) {
            nameElement.textContent = `Hello, ${user.name}`;
        }
    } catch (error) {
        console.error("Authentication check failed:", error);
    }
}

function showAuthMessage(element, message, success = false) {
    element.className = success
        ? "alert alert-success mt-3"
        : "alert alert-danger mt-3";

    element.textContent = message;
}

function setupLoginForm() {
    const form = document.getElementById("loginForm");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const button = document.getElementById("loginButton");
        const message = document.getElementById("loginMessage");

        button.disabled = true;
        message.textContent = "";

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: document.getElementById("loginEmail").value.trim(),
                    password: document.getElementById("loginPassword").value
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof result.detail === "string"
                        ? result.detail
                        : "Login failed"
                );
            }

            showAuthMessage(message, "Login successful! Redirecting...", true);

            const next = new URLSearchParams(
                window.location.search
            ).get("next");

            // Only allow internal paths to prevent open redirects.
            const destination = next &&
                next.startsWith("/") &&
                !next.startsWith("//") &&
                !next.startsWith("/\\")
                ? next
                : "/";

            window.location.assign(destination);

        } catch (error) {
            showAuthMessage(message, error.message);
            button.disabled = false;
        }
    });
}

function setupRegistrationForm() {
    const form = document.getElementById("registerForm");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const button = document.getElementById("registerButton");
        const message = document.getElementById("registerMessage");

        button.disabled = true;
        message.textContent = "";

        try {
            const response = await fetch("/users/register", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: document.getElementById("registerName").value.trim(),
                    email: document.getElementById("registerEmail").value.trim(),
                    password: document.getElementById("registerPassword").value
                })
            });

            const result = await response.json();

            if (!response.ok) {
                const detail = result.detail;

                throw new Error(
                    typeof detail === "string"
                        ? detail
                        : "Registration failed. Check your details."
                );
            }

            showAuthMessage(
                message,
                "Account created successfully! Redirecting to login...",
                true
            );

            window.location.assign("/login");

        } catch (error) {
            showAuthMessage(message, error.message);
            button.disabled = false;
        }
    });
}

function setupLogout() {
    const button = document.getElementById("logoutButton");
    if (!button) return;

    button.addEventListener("click", async () => {
        button.disabled = true;

        try {
            // Your backend uses the eventsphere_csrf cookie.
            const csrfToken = getCookie("eventsphere_csrf");

            const response = await fetch("/auth/logout", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRF-Token": csrfToken || ""
                }
            });

            if (!response.ok) {
                throw new Error("Logout failed");
            }

            window.location.assign("/login");

        } catch (error) {
            alert(error.message);
            button.disabled = false;
        }
    });
}


document.addEventListener("DOMContentLoaded", () => {
    setupPaymentPage();
    loadMyTickets();
});

function csrfHeaders(includeJson = false) {
    const headers = {
        "X-CSRF-Token": getCookie("eventsphere_csrf") || ""
    };

    if (includeJson) {
        headers["Content-Type"] = "application/json";
    }

    return headers;
}

async function readApiResponse(response) {
    const data = await response.json();

    if (!response.ok) {
        let message = "Request failed";

        if (typeof data.detail === "string") {
            message = data.detail;
        } else if (data.detail) {
            message = JSON.stringify(data.detail);
        }

        const error = new Error(message);
        error.status = response.status;
        throw error;
    }

    return data;
}

function setupPaymentPage() {
    const payButton = document.getElementById("payNowButton");
    if (!payButton) return;

    const bookingId = Number(
        window.location.pathname.split("/").pop()
    );

    const bookingLabel = document.getElementById("paymentBookingId");
    const statusLabel = document.getElementById("paymentStatus");
    const message = document.getElementById("paymentMessage");

    if (!Number.isInteger(bookingId) || bookingId <= 0) {
        payButton.disabled = true;
        message.textContent = "Invalid booking ID.";
        return;
    }

    bookingLabel.textContent = `Booking #${bookingId}`;

    payButton.addEventListener("click", async () => {
        payButton.disabled = true;
        message.className = "mt-3";
        message.textContent = "Processing simulated payment...";

        try {
            const paymentResponse = await fetch(
                `/payments/${bookingId}/simulate`,
                {
                    method: "POST",
                    credentials: "same-origin",
                    headers: csrfHeaders(true),
                    body: JSON.stringify({ success: true })
                }
            );

            const payment = await readApiResponse(paymentResponse);

            statusLabel.textContent =
                `Payment status: ${payment.status}`;

            message.textContent =
                "Payment simulation completed. Issuing tickets...";

            const ticketResponse = await fetch(
                `/tickets/issue/${bookingId}`,
                {
                    method: "POST",
                    credentials: "same-origin",
                    headers: csrfHeaders()
                }
            );

            await readApiResponse(ticketResponse);

            message.className = "alert alert-success mt-3";
            message.textContent =
                "Payment completed and QR tickets issued!";

            window.location.assign("/my-tickets");

        } catch (error) {
            message.className = "alert alert-danger mt-3";

            if (error.status === 401) {
                message.textContent = "Please log in to continue.";
            } else {
                message.textContent =
                    `${error.message}. Check My Tickets before retrying.`;
            }

            // Do not automatically repeat payment after an uncertain
            // result: the backend may already have recorded it.
        }
    });
}

async function loadMyTickets() {
    const container = document.getElementById("ticketsContainer");
    if (!container) return;

    try {
        const response = await fetch("/tickets/my", {
            credentials: "same-origin"
        });

        if (response.status === 401) {
            window.location.assign(
                "/login?next=" + encodeURIComponent("/my-tickets")
            );
            return;
        }

        const tickets = await readApiResponse(response);

        if (!Array.isArray(tickets)) {
            throw new Error("Unexpected ticket response");
        }

        container.replaceChildren();

        if (tickets.length === 0) {
            const empty = document.createElement("div");
            empty.className = "col-12";

            const alert = document.createElement("div");
            alert.className = "alert alert-info";
            alert.textContent =
                "You don't have any issued tickets yet.";

            empty.appendChild(alert);
            container.appendChild(empty);
            return;
        }

        for (const ticket of tickets) {
            const column = document.createElement("div");
            column.className = "col-md-6 col-lg-4";

            const card = document.createElement("div");
            card.className = "card shadow-sm border-0 rounded-4 h-100";

            const body = document.createElement("div");
            body.className = "card-body text-center p-4";

            const title = document.createElement("h5");
            title.className = "fw-bold";
            title.textContent = `Ticket #${ticket.id}`;

            const eventLabel = document.createElement("p");
            eventLabel.className = "text-muted";
            eventLabel.textContent = `Event ID: ${ticket.event_id}`;

            const status = document.createElement("span");
            status.className = "badge bg-primary mb-3";
            status.textContent = ticket.status || "Issued";

            const qr = document.createElement("img");
            qr.src = `/tickets/${encodeURIComponent(ticket.id)}/qr`;
            qr.alt = `QR code for ticket ${ticket.id}`;
            qr.className = "img-fluid d-block mx-auto my-3";
            qr.style.maxWidth = "200px";

            const booking = document.createElement("p");
            booking.className = "small text-muted";
            booking.textContent = `Booking #${ticket.booking_id}`;

            body.append(title, eventLabel, status, qr, booking);
            card.appendChild(body);
            column.appendChild(card);
            container.appendChild(column);
        }

    } catch (error) {
        container.replaceChildren();

        const alert = document.createElement("div");
        alert.className = "alert alert-danger";
        alert.textContent = `Unable to load tickets: ${error.message}`;

        container.appendChild(alert);
    }
}



document.addEventListener("DOMContentLoaded", () => {
    setupStaffCheckin();
});

async function setupStaffCheckin() {
    const form = document.getElementById("checkinForm");
    if (!form) return;

    const eventSelect = document.getElementById("checkinEvent");
    const tokenInput = document.getElementById("qrToken");
    const button = document.getElementById("checkinButton");
    const result = document.getElementById("checkinResult");
    const accessMessage = document.getElementById("staffAccessMessage");

    form.classList.add("d-none");

    try {
        const authResponse = await fetch("/auth/me", {
            credentials: "same-origin"
        });

        if (authResponse.status === 401) {
            window.location.assign(
                "/login?next=" +
                encodeURIComponent("/staff/checkin")
            );
            return;
        }

        const user = await readApiResponse(authResponse);

        if (!["staff", "admin"].includes(user.role)) {
            accessMessage.className = "alert alert-danger mb-3";
            accessMessage.textContent =
                "Access denied. Staff or administrator account required.";
            return;
        }

        const eventsResponse = await fetch("/events/", {
            credentials: "same-origin"
        });

        const events = await readApiResponse(eventsResponse);

        eventSelect.replaceChildren();

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Choose an event";
        eventSelect.appendChild(placeholder);

        for (const event of events) {
            const option = document.createElement("option");
            option.value = event.id;
            option.textContent = `${event.title} (ID: ${event.id})`;
            eventSelect.appendChild(option);
        }

        form.classList.remove("d-none");

    } catch (error) {
        accessMessage.className = "alert alert-danger mb-3";
        accessMessage.textContent =
            `Unable to initialize check-in: ${error.message}`;
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const eventId = Number(eventSelect.value);
        const qrToken = tokenInput.value.trim();

        if (!Number.isInteger(eventId) || eventId <= 0 ||
            qrToken.length < 10) {
            result.className = "alert alert-warning mt-4";
            result.textContent =
                "Please select an event and enter a valid QR token.";
            return;
        }

        button.disabled = true;
        result.className = "alert alert-info mt-4";
        result.textContent = "Validating ticket...";

        try {
            const response = await fetch("/checkin/", {
                method: "POST",
                credentials: "same-origin",
                headers: csrfHeaders(true),
                body: JSON.stringify({
                    qr_token: qrToken,
                    event_id: eventId
                })
            });

            const data = await readApiResponse(response);

            result.className = "alert alert-success mt-4";
            result.textContent =
                data.message || "Ticket checked in successfully!";

            tokenInput.value = "";
            tokenInput.focus();

        } catch (error) {
            result.className = "alert alert-danger mt-4";
            result.textContent =
                `Check-in failed: ${error.message}`;
        } finally {
            button.disabled = false;
        }
    });
}



document.addEventListener("DOMContentLoaded", () => {
    loadMyWaitlist();
    loadMyNotifications();
});

async function loadMyWaitlist() {
    const container = document.getElementById("waitlistContainer");
    if (!container) return;

    try {
        const response = await fetch("/waitlist/my", {
            credentials: "same-origin"
        });

        if (response.status === 401) {
            window.location.assign(
                "/login?next=" + encodeURIComponent("/my-waitlist")
            );
            return;
        }

        const entries = await readApiResponse(response);

        container.replaceChildren();

        if (entries.length === 0) {
            container.textContent = "You are not on any waitlists.";
            return;
        }

        for (const entry of entries) {
            const column = document.createElement("div");
            column.className = "col-md-6";

            const card = document.createElement("div");
            card.className = "card shadow-sm border-0 rounded-4 h-100";

            const body = document.createElement("div");
            body.className = "card-body p-4";

            const title = document.createElement("h5");
            title.textContent = `Event #${entry.event_id}`;

            const quantity = document.createElement("p");
            quantity.textContent = `Requested tickets: ${entry.quantity}`;

            const status = document.createElement("p");
            status.textContent = `Status: ${entry.status}`;

            body.append(title, quantity, status);

            if (entry.offer_expires_at) {
                const expiry = document.createElement("p");
                expiry.className = "text-muted small";
                expiry.textContent =
                    `Offer expires: ${new Date(
                        entry.offer_expires_at + (
                            entry.offer_expires_at.endsWith("Z") ? "" : "Z"
                        )
                    ).toLocaleString()}`;

                body.appendChild(expiry);
            }

            if (entry.status === "offered") {
                const button = document.createElement("button");
                button.className = "btn btn-success";
                button.textContent = "Accept Offer";

                button.addEventListener("click", async () => {
                    button.disabled = true;

                    try {
                        const response = await fetch(
                            `/waitlist/${entry.id}/accept`,
                            {
                                method: "POST",
                                credentials: "same-origin",
                                headers: csrfHeaders()
                            }
                        );

                        const result = await readApiResponse(response);

                        window.location.assign(
                            `/payment/${result.booking_id}`
                        );

                    } catch (error) {
                        alert(`Unable to accept offer: ${error.message}`);
                        button.disabled = false;
                    }
                });

                body.appendChild(button);
            }

            card.appendChild(body);
            column.appendChild(card);
            container.appendChild(column);
        }

    } catch (error) {
        container.textContent =
            `Unable to load waitlist: ${error.message}`;
    }
}

async function loadMyNotifications() {
    const container = document.getElementById("notificationsContainer");
    if (!container) return;

    try {
        const response = await fetch("/notifications/my", {
            credentials: "same-origin"
        });

        if (response.status === 401) {
            window.location.assign(
                "/login?next=" + encodeURIComponent("/my-notifications")
            );
            return;
        }

        const notifications = await readApiResponse(response);

        container.replaceChildren();

        if (notifications.length === 0) {
            container.textContent = "No notifications yet.";
            return;
        }

        for (const notification of notifications) {
            const card = document.createElement("div");
            card.className = notification.is_read
                ? "card mb-3"
                : "card mb-3 border-primary";

            const body = document.createElement("div");
            body.className = "card-body";

            const title = document.createElement("h5");
            title.textContent = notification.title;

            const message = document.createElement("p");
            message.textContent = notification.message;

            body.append(title, message);

            if (!notification.is_read) {
                const button = document.createElement("button");
                button.className = "btn btn-sm btn-outline-primary";
                button.textContent = "Mark as Read";

                button.addEventListener("click", async () => {
                    button.disabled = true;

                    try {
                        const response = await fetch(
                            `/notifications/${notification.id}/read`,
                            {
                                method: "POST",
                                credentials: "same-origin",
                                headers: csrfHeaders()
                            }
                        );

                        await readApiResponse(response);
                        loadMyNotifications();

                    } catch (error) {
                        alert(`Unable to update notification: ${error.message}`);
                        button.disabled = false;
                    }
                });

                body.appendChild(button);
            }

            card.appendChild(body);
            container.appendChild(card);
        }

    } catch (error) {
        container.textContent =
            `Unable to load notifications: ${error.message}`;
    }
}


document.addEventListener("DOMContentLoaded", () => {
    setupPrivateHire();
    loadMyPrivateHires();
    loadAdminHires();
});

function hireDate(value) {
    if (!value) return "N/A";
    return new Date(value.endsWith("Z") ? value : value + "Z")
        .toLocaleString();
}

function addHireText(parent, tag, value, className = "") {
    const element = document.createElement(tag);
    element.textContent = value;
    element.className = className;
    parent.appendChild(element);
    return element;
}

async function setupPrivateHire() {
    const form = document.getElementById("privateHireForm");
    if (!form) return;

    const venueSelect = document.getElementById("hireVenue");
    const button = document.getElementById("hireSubmitButton");
    const result = document.getElementById("hireResult");

    try {
        const response = await fetch("/venues/", {
            credentials: "same-origin"
        });

        const venues = await readApiResponse(response);

        venueSelect.replaceChildren();

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select a venue";
        venueSelect.appendChild(placeholder);

        for (const venue of venues) {
            if (venue.private_hire_enabled === false) continue;

            const option = document.createElement("option");
            option.value = venue.id;
            option.textContent =
                `${venue.name} — Capacity: ${venue.capacity}`;
            venueSelect.appendChild(option);
        }

    } catch (error) {
        result.className = "alert alert-danger mt-3";
        result.textContent = `Unable to load venues: ${error.message}`;
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const start = document.getElementById("hireStart").value;
        const end = document.getElementById("hireEnd").value;
        const guests = Number(document.getElementById("hireGuests").value);
        const purpose = document.getElementById("hirePurpose").value.trim();

        if (!start || !end || new Date(end) <= new Date(start)) {
            result.className = "alert alert-warning mt-3";
            result.textContent = "End time must be after start time.";
            return;
        }

        if (!Number.isInteger(guests) || guests <= 0) {
            result.textContent = "Enter a valid guest count.";
            return;
        }

        button.disabled = true;
        result.textContent = "Submitting request...";

        try {
            const response = await fetch("/private-hires/request", {
                method: "POST",
                credentials: "same-origin",
                headers: csrfHeaders(true),
                body: JSON.stringify({
                    venue_id: Number(venueSelect.value),
                    start_time: new Date(start).toISOString(),
                    end_time: new Date(end).toISOString(),
                    purpose: purpose,
                    guest_count: guests
                })
            });

            if (response.status === 401) {
                window.location.assign(
                    "/login?next=" + encodeURIComponent("/private-hire")
                );
                return;
            }

            const data = await readApiResponse(response);

            if (data.decision === "PROPOSE") {
                result.className = "alert alert-warning mt-3";
                result.textContent =
                    "The requested slot is unavailable. " +
                    JSON.stringify(data);
                return;
            }

            result.className = "alert alert-success mt-3";
            result.textContent =
                `Request submitted successfully. Decision: ${data.decision}`;

            form.reset();

        } catch (error) {
            result.className = "alert alert-danger mt-3";
            result.textContent = error.message;
        } finally {
            button.disabled = false;
        }
    });
}

async function loadMyPrivateHires() {
    const container = document.getElementById("myHiresContainer");
    if (!container) return;

    try {
        const response = await fetch("/private-hires/my", {
            credentials: "same-origin"
        });

        if (response.status === 401) {
            window.location.assign(
                "/login?next=" + encodeURIComponent("/my-private-hires")
            );
            return;
        }

        const hires = await readApiResponse(response);
        container.replaceChildren();

        if (hires.length === 0) {
            container.textContent = "No private hire requests yet.";
            return;
        }

        for (const hire of hires) {
            const column = document.createElement("div");
            column.className = "col-md-6";

            const card = document.createElement("div");
            card.className = "card shadow-sm border-0 rounded-4 h-100";

            const body = document.createElement("div");
            body.className = "card-body p-4";

            addHireText(body, "h5", `Hire #${hire.id}`, "fw-bold");
            addHireText(body, "p", `Venue ID: ${hire.venue_id}`);
            addHireText(body, "p", `Purpose: ${hire.purpose}`);
            addHireText(body, "p", `Guests: ${hire.guest_count}`);
            addHireText(body, "p", `Start: ${hireDate(hire.start_time)}`);
            addHireText(body, "p", `End: ${hireDate(hire.end_time)}`);
            addHireText(
                body, "p",
                `Total: LKR ${Number(hire.total_price).toFixed(2)}`
            );
            addHireText(body, "p", `Status: ${hire.status}`, "fw-semibold");

            card.appendChild(body);
            column.appendChild(card);
            container.appendChild(column);
        }

    } catch (error) {
        container.textContent =
            `Unable to load requests: ${error.message}`;
    }
}

async function loadAdminHires() {
    const container = document.getElementById("adminHiresContainer");
    if (!container) return;

    try {
        const profileResponse = await fetch("/auth/me", {
            credentials: "same-origin"
        });

        if (profileResponse.status === 401) {
            window.location.assign(
                "/login?next=" + encodeURIComponent("/admin/hires")
            );
            return;
        }

        const user = await readApiResponse(profileResponse);

        if (user.role !== "admin") {
            container.textContent = "Admin access required.";
            return;
        }

        const response = await fetch("/private-hires/pending", {
            credentials: "same-origin"
        });

        const hires = await readApiResponse(response);
        container.replaceChildren();

        if (hires.length === 0) {
            container.textContent = "No pending hire requests.";
            return;
        }

        for (const hire of hires) {
            const column = document.createElement("div");
            column.className = "col-md-6";

            const card = document.createElement("div");
            card.className = "card shadow-sm border-0 rounded-4 h-100";

            const body = document.createElement("div");
            body.className = "card-body p-4";

            addHireText(body, "h5", `Hire #${hire.id}`, "fw-bold");
            addHireText(body, "p", `User ID: ${hire.user_id}`);
            addHireText(body, "p", `Venue ID: ${hire.venue_id}`);
            addHireText(body, "p", `Purpose: ${hire.purpose}`);
            addHireText(body, "p", `Guests: ${hire.guest_count}`);
            addHireText(body, "p", `Start: ${hireDate(hire.start_time)}`);
            addHireText(body, "p", `End: ${hireDate(hire.end_time)}`);
            addHireText(
                body, "p",
                `Total: LKR ${Number(hire.total_price).toFixed(2)}`
            );

            const approve = document.createElement("button");
            approve.className = "btn btn-success me-2";
            approve.textContent = "Approve";

            const reject = document.createElement("button");
            reject.className = "btn btn-outline-danger";
            reject.textContent = "Reject";

            async function decide(approved) {
                approve.disabled = true;
                reject.disabled = true;

                try {
                    const response = await fetch(
                        `/private-hires/${hire.id}/decision`,
                        {
                            method: "POST",
                            credentials: "same-origin",
                            headers: csrfHeaders(true),
                            body: JSON.stringify({ approve: approved })
                        }
                    );

                    await readApiResponse(response);
                    await loadAdminHires();

                } catch (error) {
                    alert(`Decision failed: ${error.message}`);
                    approve.disabled = false;
                    reject.disabled = false;
                }
            }

            approve.addEventListener("click", () => decide(true));
            reject.addEventListener("click", () => decide(false));

            body.append(approve, reject);
            card.appendChild(body);
            column.appendChild(card);
            container.appendChild(column);
        }

    } catch (error) {
        container.textContent =
            `Unable to load pending hires: ${error.message}`;
    }
}


document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("adminStats")) {
        initializeAdminDashboard();
    }
});

let agentLogsOffset = 0;
const agentLogsPageSize = 25;

async function initializeAdminDashboard() {
    const errorBox = document.getElementById("adminDashboardError");

    try {
        const authResponse = await fetch("/auth/me", {
            credentials: "same-origin"
        });

        if (authResponse.status === 401) {
            window.location.assign("/login");
            return;
        }

        const user = await readApiResponse(authResponse);

        if (user.role !== "admin") {
            errorBox.className = "alert alert-danger";
            errorBox.textContent = "Admin access required.";
            return;
        }

        document.getElementById("refreshAgentLogs")
            .addEventListener("click", () => loadAgentLogs());

        document.getElementById("previousAgentLogs")
            .addEventListener("click", () => {
                agentLogsOffset = Math.max(
                    0, agentLogsOffset - agentLogsPageSize
                );
                loadAgentLogs();
            });

        document.getElementById("nextAgentLogs")
            .addEventListener("click", () => {
                agentLogsOffset += agentLogsPageSize;
                loadAgentLogs();
            });

        await Promise.all([
            loadAdminStats(),
            loadRecentBookings(),
            loadAgentLogs()
        ]);

    } catch (error) {
        errorBox.className = "alert alert-danger";
        errorBox.textContent = error.message;
    }
}

async function loadAdminStats() {
    const response = await fetch("/admin/stats", {
        credentials: "same-origin"
    });
    const stats = await readApiResponse(response);

    const container = document.getElementById("adminStats");
    container.replaceChildren();

    const items = [
        ["Users", stats.users],
        ["Venues", stats.venues],
        ["Events", stats.events],
        ["Bookings", stats.bookings],
        ["Tickets", stats.tickets],
        ["Private Hires", stats.private_hires],
        ["Waitlist Entries", stats.waitlist_entries],
        ["Agent Messages", stats.agent_messages],
        ["Revenue (LKR)", Number(stats.revenue).toLocaleString()]
    ];

    for (const [label, value] of items) {
        const col = document.createElement("div");
        col.className = "col-6 col-md-4 col-xl-3";

        const card = document.createElement("div");
        card.className = "card shadow-sm h-100";

        const body = document.createElement("div");
        body.className = "card-body";

        const heading = document.createElement("p");
        heading.className = "text-muted mb-1";
        heading.textContent = label;

        const number = document.createElement("h3");
        number.className = "fw-bold";
        number.textContent = value;

        body.append(heading, number);
        card.appendChild(body);
        col.appendChild(card);
        container.appendChild(col);
    }

    drawStatusChart("bookingStatusChart", stats.booking_statuses);
    drawStatusChart("paymentStatusChart", stats.payment_statuses);
}

function drawStatusChart(canvasId, statuses) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;

    const labels = Object.keys(statuses);
    const values = Object.values(statuses);

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "#198754",
                    "#ffc107",
                    "#dc3545",
                    "#0d6efd",
                    "#6c757d"
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom" }
            }
        }
    });
}

function adminTableCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value ?? "";
    row.appendChild(cell);
    return cell;
}

async function loadRecentBookings() {
    const response = await fetch("/admin/recent-bookings", {
        credentials: "same-origin"
    });
    const bookings = await readApiResponse(response);
    const tbody = document.getElementById("recentBookingsBody");

    tbody.replaceChildren();

    for (const booking of bookings) {
        const row = document.createElement("tr");

        adminTableCell(row, booking.id);
        adminTableCell(row, booking.user_id);
        adminTableCell(row, booking.event_id);
        adminTableCell(row, booking.quantity);
        adminTableCell(
            row, `LKR ${Number(booking.total_amount).toFixed(2)}`
        );
        adminTableCell(row, booking.status);

        tbody.appendChild(row);
    }
}

async function loadAgentLogs() {
    const response = await fetch(
        `/admin/agent-logs?limit=${agentLogsPageSize}&offset=${agentLogsOffset}`,
        { credentials: "same-origin" }
    );

    const data = await readApiResponse(response);
    const tbody = document.getElementById("agentLogsBody");

    tbody.replaceChildren();

    for (const message of data.messages) {
        const row = document.createElement("tr");

        adminTableCell(row, message.id);
        adminTableCell(row, message.sender);
        adminTableCell(row, message.receiver);
        adminTableCell(row, message.performative);
        adminTableCell(row, message.conversation_id);

        const cell = document.createElement("td");
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        const pre = document.createElement("pre");

        summary.textContent = "View";
        pre.className = "small mt-2";
        pre.style.whiteSpace = "pre-wrap";
        pre.style.maxWidth = "350px";
        pre.textContent = JSON.stringify(message.content, null, 2);

        details.append(summary, pre);
        cell.appendChild(details);
        row.appendChild(cell);

        tbody.appendChild(row);
    }

    document.getElementById("agentLogsCount").textContent =
        `Showing ${data.messages.length} of ${data.total} messages ` +
        `(starting at ${agentLogsOffset + 1})`;

    document.getElementById("previousAgentLogs").disabled =
        agentLogsOffset === 0;

    document.getElementById("nextAgentLogs").disabled =
        agentLogsOffset + data.messages.length >= data.total;
}
