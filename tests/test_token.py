from pages.login_page import LoginPage
from pages.token_page import TokenPage


def test_generate_token_page(driver):

    login = LoginPage(driver)

    login.login(
        "student@test.com",
        "Student@123"
    )

    driver.get("http://127.0.0.1:5000/student/generate-token")

    token = TokenPage(driver)

    # Verify page actually loaded
    assert token.driver.current_url.endswith("/student/generate-token")

    # Verify Department dropdown
    assert token.driver.find_element(
        *token.DEPARTMENT_SELECT
    ).is_displayed()

    # Verify Service dropdown
    assert token.driver.find_element(
        *token.SERVICE_SELECT
    ).is_displayed()

    # Verify Generate Token button
    assert token.driver.find_element(
        *token.GENERATE_BUTTON
    ).is_displayed()