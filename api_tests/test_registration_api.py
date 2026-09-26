import requests
import time


def test_valid_registration_api():
    url = "http://127.0.0.1:5000/register"

    unique_email = f"api_test_{int(time.time())}@test.com"

    data = {
        "name": "API Test User",
        "email": unique_email,
        "phone": "9876543210",
        "password": "Test@123",
        "confirm_password": "Test@123"
    }

    response = requests.post(
        url,
        data=data,
        allow_redirects=False
    )

    print("Registration Status:", response.status_code)
    print("Location:", response.headers.get("Location"))

    assert response.status_code == 302
    assert response.headers.get("Location") == "/login"


def test_registration_password_mismatch_api():
    url = "http://127.0.0.1:5000/register"

    data = {
        "name": "API Test User",
        "email": f"mismatch_{int(time.time())}@test.com",
        "phone": "9876543211",
        "password": "Test@123",
        "confirm_password": "Wrong@123"
    }

    response = requests.post(
        url,
        data=data
    )

    print("Password Mismatch Status:", response.status_code)

    assert response.status_code == 400