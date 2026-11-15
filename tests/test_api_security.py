
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

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF token missing"


def test_unauthenticated_booking(client):
    response = client.post(
        "/bookings/",
        json={
            "event_id": 1,
            "quantity": 1
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF token missing"

   
def test_checkin_without_login_but_with_csrf(client):
    client.cookies.set("eventsphere_csrf", "test-csrf-token")

    response = client.post(
        "/checkin/",
        json={
            "event_id": 1,
            "qr_token": "invalid-test-token"
        },
        headers={"X-CSRF-Token": "test-csrf-token"}
    )

    assert response.status_code == 401


def test_booking_without_login_but_with_csrf(client):
    client.cookies.set("eventsphere_csrf", "test-csrf-token")

    response = client.post(
        "/bookings/",
        json={
            "event_id": 1,
            "quantity": 1
        },
        headers={"X-CSRF-Token": "test-csrf-token"}
    )

    assert response.status_code == 401
