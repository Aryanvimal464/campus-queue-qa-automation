import requests


BASE_URL = "http://127.0.0.1:5000"


def staff_login():
    session = requests.Session()

    login_data = {
        "email": "staff@test.com",
        "password": "Staff@123"
    }

    response = session.post(
        f"{BASE_URL}/login",
        data=login_data,
        allow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers.get("Location") == "/staff/dashboard"

    return session


def test_staff_dashboard_api():
    session = staff_login()

    response = session.get(
        f"{BASE_URL}/staff/dashboard"
    )

    print("Dashboard Status:", response.status_code)

    assert response.status_code == 200


def test_staff_queue_api():
    session = staff_login()

    response = session.get(
        f"{BASE_URL}/staff/queue"
    )

    print("Queue Status:", response.status_code)

    assert response.status_code == 200


def test_staff_call_next_api():
    session = staff_login()

    response = session.post(
        f"{BASE_URL}/staff/call-next",
        allow_redirects=False
    )

    print("Call Next Status:", response.status_code)
    print("Call Next Location:",
          response.headers.get("Location"))

    assert response.status_code == 302


def test_staff_history_api():
    session = staff_login()

    response = session.get(
        f"{BASE_URL}/staff/history"
    )

    print("History Status:", response.status_code)

    assert response.status_code == 200


def test_student_cannot_access_staff_dashboard():
    session = requests.Session()

    login_data = {
        "email": "student@test.com",
        "password": "Student@123"
    }

    login_response = session.post(
        f"{BASE_URL}/login",
        data=login_data,
        allow_redirects=False
    )

    assert login_response.status_code == 302

    response = session.get(
        f"{BASE_URL}/staff/dashboard",
        allow_redirects=False
    )

    print("Unauthorized Status:", response.status_code)
    print("Unauthorized Location:",
          response.headers.get("Location"))

    assert response.status_code in [302, 403]