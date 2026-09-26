from selenium.webdriver.common.by import By


class RegistrationPage:

    NAME = (By.ID, "name")
    EMAIL = (By.ID, "email")
    PHONE = (By.ID, "phone")
    PASSWORD = (By.ID, "password")
    CONFIRM_PASSWORD = (By.ID, "confirm_password")
    REGISTER_BUTTON = (By.ID, "register-button")
    LOGIN_LINK = (By.ID, "go-to-login-link")
    REGISTRATION_ERROR = (By.ID, "registration-error")

    def __init__(self, driver):
        self.driver = driver

    def enter_name(self, name):
        self.driver.find_element(*self.NAME).send_keys(name)

    def enter_email(self, email):
        self.driver.find_element(*self.EMAIL).send_keys(email)

    def enter_phone(self, phone):
        self.driver.find_element(*self.PHONE).send_keys(phone)

    def enter_password(self, password):
        self.driver.find_element(*self.PASSWORD).send_keys(password)

    def enter_confirm_password(self, confirm_password):
        self.driver.find_element(*self.CONFIRM_PASSWORD).send_keys(confirm_password)

    def click_register(self):
        self.driver.find_element(*self.REGISTER_BUTTON).click()

    def register(self, name, email, phone, password, confirm_password):
        self.enter_name(name)
        self.enter_email(email)
        self.enter_phone(phone)
        self.enter_password(password)
        self.enter_confirm_password(confirm_password)
        self.click_register()

    def get_error_message(self):
        return self.driver.find_element(*self.REGISTRATION_ERROR).text