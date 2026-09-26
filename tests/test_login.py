from pages.login_page import LoginPage


def test_valid_login(driver):
    login_page = LoginPage(driver)

    login_page.login(
        "student@test.com",
        "Student@123"
    )

    print("AFTER LOGIN URL:", driver.current_url)

    assert "dashboard" in driver.current_url.lower()