import requests


BASE_URL = "http://127.0.0.1:5000"


def test_generate_token_page_api():
    session = requests.Session()

    # Student login
    login_data = {
        "email": "student@test.com",
        "password": "Student@123"
    }

    login_response = session.post(
        f"{BASE_URL}/login",
        data=login_data,
        allow_redirects=False
    )

    print("Login Status:", login_response.status_code)
    print("Login Location:", login_response.headers.get("Location"))

    assert login_response.status_code == 302
    assert login_response.headers.get("Location") == "/student/dashboard"

    # Open generate token page
    response = session.get(
        f"{BASE_URL}/student/generate-token"
    )

    print("Token Page Status:", response.status_code)
    print("Token Page URL:", response.url)

    assert response.status_code == 200
    assert "Generate Token" in response.text


def test_generate_token_without_login():
    session = requests.Session()

    response = session.get(
        f"{BASE_URL}/student/generate-token",
        allow_redirects=False
    )

    print("Unauthenticated Status:", response.status_code)
    print("Unauthenticated Location:",
          response.headers.get("Location"))

    assert response.status_code == 302
def test_staff_queue_api():
    session = requests.Session()

    login_data = {
        "email": "staff@test.com",
        "password": "Staff@123"
    }

    login_response = session.post(
        f"{BASE_URL}/login",
        data=login_data,
        allow_redirects=False
    )

    assert login_response.status_code == 302
    assert login_response.headers.get("Location") == "/staff/dashboard"

    response = session.get(
        f"{BASE_URL}/staff/queue"
    )

    print("Staff Queue Status:", response.status_code)

    assert response.status_code == 200


def test_staff_call_next_api():
    session = requests.Session()

    login_data = {
        "email": "staff@test.com",
        "password": "Staff@123"
    }

    login_response = session.post(
        f"{BASE_URL}/login",
        data=login_data,
        allow_redirects=False
    )

    assert login_response.status_code == 302

    response = session.post(
        f"{BASE_URL}/staff/call-next",
        allow_redirects=False
    )

    print("Call Next Status:", response.status_code)
    print("Call Next Location:",
          response.headers.get("Location"))

    assert response.status_code == 302