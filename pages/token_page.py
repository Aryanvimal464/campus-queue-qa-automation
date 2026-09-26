from selenium.webdriver.common.by import By


class TokenPage:

    DEPARTMENT_SELECT = (By.ID, "department-select")
    SERVICE_SELECT = (By.ID, "service-select")
    GENERATE_BUTTON = (By.ID, "generate-token-button")
    TOKEN_ERROR = (By.ID, "token-error")
    TOKEN_SUCCESS = (By.ID, "token-success")
    ACTIVE_TOKEN_WARNING = (By.ID, "active-token-warning")

    def __init__(self, driver):
        self.driver = driver

    def select_department(self, department_id):
        from selenium.webdriver.support.ui import Select

        department = Select(
            self.driver.find_element(*self.DEPARTMENT_SELECT)
        )
        department.select_by_value(str(department_id))

    def select_service(self, service_id):
        from selenium.webdriver.support.ui import Select

        service = Select(
            self.driver.find_element(*self.SERVICE_SELECT)
        )
        service.select_by_value(str(service_id))

    def click_generate(self):
        self.driver.find_element(*self.GENERATE_BUTTON).click()

    def is_error_displayed(self):
        return len(self.driver.find_elements(*self.TOKEN_ERROR)) > 0

    def is_success_displayed(self):
        return len(self.driver.find_elements(*self.TOKEN_SUCCESS)) > 0

    def is_active_token_warning_displayed(self):
        return len(
            self.driver.find_elements(*self.ACTIVE_TOKEN_WARNING)
        ) > 0