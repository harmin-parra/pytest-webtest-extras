import base64
import html
# import importlib
from typing import Union
from . import utils
from selenium.webdriver.remote.webelement import WebElement
from playwright.sync_api import Page


# Counter used for image and page source files naming
count = 0


def counter():
    """ Returns a suffix used for image and webpage source file naming """
    global count
    count += 1
    return count


class Extras:
    """
    Class to hold pytest-html 'extras' to be added for each test in the HTML report.
    """

    def __init__(self, report_folder, fx_screenshots, fx_comments, fx_sources, report_allure):
        """
        Args:
            report_folder (str): The 'report_folder' fixture.
            fx_screenshots (str): The 'screenshots' fixture.
            fx_comments (bool): The 'comments' fixture.
            fx_sources (bool): The 'sources' fixture.
            report_allure (bool): Whether the allure-pytest plugin is being used.
        """
        self.images = []
        self.sources = []
        self.comments = []
        self._fx_screenshots = fx_screenshots
        self._fx_comments = fx_comments
        self._fx_sources = fx_sources
        self._folder = report_folder
        self._allure = report_allure


    def save_screenshot(self, image: Union[bytes, str], comment=None, source=None, escape_html=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        The screenshot is saved in <forder_report>/screenshots folder.
        The webpage source is saved in <forder_report>/sources folder.
        Adds the screenshot and source to Allure report, if applicable.

        Args:
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

        # Add extras to Allure report if allure-pytest plugin is being used.
        # if importlib.util.find_spec('allure') is not None:
        if self._allure:
            import allure
            allure.attach(image, name=comment, attachment_type=allure.attachment_type.PNG)
            # Attach the webpage source
            if source is not None:
                allure.attach(source, name="page source", attachment_type=allure.attachment_type.TEXT)


    def screenshot_for_selenium(self, target, comment=None, full_page=True, escape_html=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.

        Args:
            target (WebDriver | WebElement): The target of the screenshot.
            comment (str): The comment for the screenshot to take.
            full_page (bool): Whether to take a full-page screenshot if the target is a WebDriver instance.
                              Defaults to True.
        """
        from selenium.webdriver.chrome.webdriver import WebDriver as WebDriver_Chrome
        from selenium.webdriver.chromium.webdriver import ChromiumDriver as WebDriver_Chromium
        from selenium.webdriver.edge.webdriver import WebDriver as WebDriver_Edge

        source = None
        if self._fx_screenshots == 'none':
            return
        if isinstance(target, WebElement):
            image = target.screenshot_as_png
        else:
            if full_page is True:
                if hasattr(target, "get_full_page_screenshot_as_png"):
                    image = target.get_full_page_screenshot_as_png()
                else:
                    if type(target) in (WebDriver_Chrome, WebDriver_Chromium, WebDriver_Edge):
                        try:
                            image = utils.get_full_page_screenshot_chromium(target)
                        except:
                            image = target.get_screenshot_as_png()
                    else:
                        image = target.get_screenshot_as_png()
            else:
                image = target.get_screenshot_as_png()
            if self._fx_sources:
                source = target.page_source
        self.save_screenshot(image, comment, source, escape_html)


    def screenshot_for_playwright(self, target, comment=None, full_page=True, escape_html=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.

        Args:
            target (Page | Locator): The target of the screenshot.
            comment (str): The comment for the screenshot to take.
            full_page (bool): Whether to take a full-page screenshot if the target is a Page instance.
                              Defaults to True.
        """
        source = None
        if self._fx_screenshots == 'none':
            return
        if isinstance(target, Page):
            image = target.screenshot(full_page=full_page)
            if self._fx_sources:
                source = target.content()
        else:
            image = target.screenshot()
        self.save_screenshot(image, comment, source, escape_html)
