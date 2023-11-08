from selenium.webdriver.chrome.webdriver import WebDriver as WebDriver_Chrome
from selenium.webdriver.common.by import By


def test_with_selenium(report_extras):
    """
    This is a test using Selenium
    """
    driver = WebDriver_Chrome()
    driver.get("https://www.selenium.dev/selenium/web/web-form.html")
    report_extras.save_screenshot_for_selenium(driver, "Get the webpage to test")
    driver.find_element(By.ID, "my-text-id").send_keys("Hello World!")
    report_extras.save_screenshot_for_selenium(driver, "Set input text")
    driver.find_element(By.NAME, "my-password").send_keys("password")
    report_extras.save_screenshot_for_selenium(driver, "Set password")
    driver.find_element(By.CLASS_NAME, "btn").click()
    report_extras.save_screenshot_for_selenium(driver, "Submit the form")


def test_with_playwright(report_extras):
    """
    This is a test using Playwright
    """
    pass
