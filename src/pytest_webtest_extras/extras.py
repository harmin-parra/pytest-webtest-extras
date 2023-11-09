import base64
import html
from typing import Union
from . import utils


# Counter used for image and page source files naming
count = 0


def counter():
    """ Returns a suffix used for image and page source file naming """
    global count
    count += 1
    return count


class Extras:
    """
    Class to hold pytest-html 'extras' to be added for each test in the HTML report.
    """

    def __init__(self, report_folder, fx_screenshots, fx_comments, fx_sources, fx_allure):
        self.images = []
        self.sources = []
        self.comments = []
        self._fx_screenshots = fx_screenshots
        self._fx_comments = fx_comments
        self._fx_sources = fx_sources
        self._folder = report_folder
        self._fx_allure = fx_allure

    def save_screenshot(self, image: Union[bytes, str], comment=None, source=None, escape_html=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        The screenshot is saved in <forder_report>/screenshots folder.
        The webpage source is saved in <forder_report>/sources folder.
        Adds the screenshot and source to Allure report, if applicable.
        
        image (bytes | str): The screenshot as bytes or base64 string.
        comment (str): The comment of the screenshot.
        source (str): The webpage source code.
        escape_html (bool): Whether to escape HTML characters in the comment.
        """
        if self._fx_screenshots == 'none':
            return
        index = counter()
        if isinstance(image, str):
            try:
                image = base64.b64decode(image.encode())
            except:
                image = None
        link_image = utils.save_image(self._folder, index, image)
        self.images.append(link_image)
        link_source = None
        if source is not None:
            link_source = utils.save_source(self._folder, index, source)
        self.sources.append(link_source)
        if self._fx_comments:
            comment = "" if comment is None else comment
            comment = html.escape(comment, quote=True) if escape_html else comment
        self.comments.append(comment)

        # Add extras to Allure report
        if self._fx_allure:
            import allure
            filename = f"image-{index}"
            # If there was an error taking the screenshot?
            if "error.png" in link_image:
                filename += " (screenshot error)"
                # Let's attach a 1x1 white pixel as image instead
                image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
                image = base64.b64decode(image.encode())
            allure.attach(image, name=filename, attachment_type=allure.attachment_type.PNG)
            if comment is not None and self._fx_comments:
                allure.attach(comment, name=f"comment-{index}", attachment_type=allure.attachment_type.TEXT)
            if source is not None:
                allure.attach(source, name=f"source-{index}", attachment_type=allure.attachment_type.TEXT)

    def save_screenshot_for_selenium(self, driver, comment=None, full_page=True, escape_html=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        
        driver (WebDriver): The webdriver.
        comment (str): The comment for the screenshot to take.
        full_page (bool): Whether to take a full-page screenshot. Defaults to True.
        """
        from selenium.webdriver.chrome.webdriver import WebDriver as WebDriver_Chrome
        from selenium.webdriver.chromium.webdriver import ChromiumDriver as WebDriver_Chromium
        from selenium.webdriver.edge.webdriver import WebDriver as WebDriver_Edge

        if self._fx_screenshots == 'none':
            return
        if full_page:
            if hasattr(driver, "get_full_page_screenshot_as_png"):
                image = driver.get_full_page_screenshot_as_png()
            else:
                if type(driver) in (WebDriver_Chrome, WebDriver_Chromium, WebDriver_Edge):
                    try:
                        image = utils.get_full_page_screenshot_chromium(driver)
                    except:
                        image = driver.get_screenshot_as_png()
                else:
                    image = driver.get_screenshot_as_png()
        else:
            image = driver.get_screenshot_as_png()
        source = None
        if self._fx_sources:
            source = driver.page_source
        self.save_screenshot(image, comment, source, escape_html)

    def save_screenshot_for_playwright(self, page, comment=None, full_page=True, escape_html=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        
        page (Page): The page.
        comment (str): The comment for the screenshot to take.
        full_page (bool): Whether to take a full-page screenshot. Defaults to True.
        """
        if self._fx_screenshots == 'none':
            return
        image = page.screenshot(full_page=full_page)
        source = None
        if self._fx_sources:
            source = page.content()
        self.save_screenshot(image, comment, source, escape_html)
