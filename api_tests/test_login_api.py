import requests


def test_login_api():
    url = "http://127.0.0.1:5000/login"

    data = {
        "email": "student@test.com",
        "password": "Student@123"
    }

    response = requests.post(
        url,
        data=data,
        allow_redirects=False
    )

    print("Status Code:", response.status_code)
    print("Location:", response.headers.get("Location"))

    assert response.status_code == 302
    assert response.headers.get("Location") == "/student/dashboard"


def test_invalid_login_api():
    url = "http://127.0.0.1:5000/login"

    data = {
        "email": "student@test.com",
        "password": "WrongPassword123"
    }

    response = requests.post(
        url,
        data=data,
        allow_redirects=False
    )

    print("Invalid Login Status:", response.status_code)

    assert response.status_code == 401