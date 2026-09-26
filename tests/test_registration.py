import time
from pages.registration_page import RegistrationPage


def test_valid_registration(driver):
    driver.get("http://127.0.0.1:5000/register")

    registration = RegistrationPage(driver)

    unique_email = f"automation_{int(time.time())}@test.com"

    registration.register(
        "Automation Test User",
        unique_email,
        "9876543212",
        "Test@123",
        "Test@123"
    )

    error_elements = driver.find_elements(
        *registration.REGISTRATION_ERROR
    )

    visible_errors = [
        element
        for element in error_elements
        if element.is_displayed() and element.text.strip()
    ]

    assert len(visible_errors) == 0


def test_registration_password_mismatch(driver):
    driver.get("http://127.0.0.1:5000/register")

    registration = RegistrationPage(driver)

    registration.register(
        "Test User",
        "mismatch_987654@test.com",
        "9876543211",
        "Test@123",
        "Wrong@123"
    )

    assert "registration-error" in driver.page_source