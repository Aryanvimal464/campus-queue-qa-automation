from selenium.webdriver.common.by import By


class StudentPage:

    WELCOME_HEADING = (By.ID, "welcome-heading")
    CURRENT_TOKEN = (By.ID, "current-token-number")
    TOKEN_STATUS = (By.ID, "current-token-status")
    QUEUE_POSITION = (By.ID, "queue-position")
    ESTIMATED_WAIT = (By.ID, "estimated-wait-time")
    VIEW_QUEUE_BUTTON = (By.ID, "view-queue-button")
    CANCEL_TOKEN_BUTTON = (By.ID, "cancel-token-button")
    GENERATE_TOKEN_BUTTON = (By.ID, "generate-token-button")

    def __init__(self, driver):
        self.driver = driver

    def get_welcome_text(self):
        return self.driver.find_element(*self.WELCOME_HEADING).text

    def is_dashboard_displayed(self):
        return self.driver.find_element(*self.WELCOME_HEADING).is_displayed()

    def click_generate_token(self):
        self.driver.find_element(*self.GENERATE_TOKEN_BUTTON).click()

    def click_view_queue(self):
        self.driver.find_element(*self.VIEW_QUEUE_BUTTON).click()

    def click_cancel_token(self):
        self.driver.find_element(*self.CANCEL_TOKEN_BUTTON).click()

    def get_token_number(self):
        return self.driver.find_element(*self.CURRENT_TOKEN).text

    def get_token_status(self):
        return self.driver.find_element(*self.TOKEN_STATUS).text