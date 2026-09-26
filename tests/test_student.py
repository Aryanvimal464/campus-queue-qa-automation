from pages.login_page import LoginPage
from pages.student_page import StudentPage


def test_student_dashboard(driver):

    login = LoginPage(driver)

    login.login(
        "student@test.com",
        "Student@123"
    )

    student = StudentPage(driver)

    assert student.is_dashboard_displayed()
    assert "Welcome" in student.get_welcome_text()
from pages.login_page import LoginPage
from pages.student_page import StudentPage


def test_student_dashboard(driver):

    login = LoginPage(driver)

    login.login(
        "student@test.com",
        "Student@123"
    )

    student = StudentPage(driver)

    assert student.is_dashboard_displayed()
    assert "Welcome" in student.get_welcome_text()