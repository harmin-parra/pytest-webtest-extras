from . import utils


# Counter used for image and page source files naming
count = 0


def counter():
    """ Returns a suffix used for image and page source file naming """
    global count
    count += 1
    return count


class Extras():
    """
    Class to hold pytest-html 'extras' to be added for each test in the HTML report
    """

    def __init__(self, report_folder, fx_screenshots, fx_comments, fx_sources):
        self.images = []
        self.sources = []
        self.comments = []
        self._fx_screenshots = fx_screenshots
        self._fx_comments = fx_comments
        self._fx_sources = fx_sources
        self._folder = report_folder

    def save_extras(self, image: bytes, comment=None, source=None):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        The screenshot is saved in <forder_report>/screenshots folder.
        The webpage source is saved in <forder_report>/sources folder.
        
        image (bytes): The screenshot.
        comment (str): The comment of the screenshot.
        source (str): The webpage source code.
        """
        if self._fx_screenshots == 'none':
            return
        index = counter()
        link_image = utils.save_image(self._folder, index, image)
        self.images.append(link_image)
        link_source = None
        if source is not None:
            link_source = utils.save_source(self._folder, index, source)
        self.sources.append(link_source)
        if self._fx_comments:
            comment = "" if comment is None else comment
            self.comments.append(comment)

    def save_for_selenium(self, driver, comment=None, full_page=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        
        driver (WebDriver): The webdriver.
        comment (str): The comment for the screenshot to take.
        full_page (bool): Whether to take a full-page screenshot.
            Only works for Firefox.
            Defaults to True.
        """
        from selenium.webdriver.remote.webdriver import WebDriver
        if self._fx_screenshots == 'none':
            return
        if hasattr(driver, "get_full_page_screenshot_as_png") and full_page:
            image = driver.get_full_page_screenshot_as_png()
        else:
            image = driver.get_screenshot_as_png()
        source = None
        if self._fx_sources:
            source = driver.page_source
        self.save_extras(image, comment, source)

    def save_for_playwright(self, page, comment=None, full_page=True):
        """
        Saves the pytest-html 'extras': screenshot, comment and webpage source.
        
        page (Page): The page.
        comment (str): The comment for the screenshot to take.
        full_page (bool): Whether to take a full-page screenshot.
                          Defaults to True.
        """
        if self._fx_screenshots == 'none':
            return
        image = page.screenshot(full_page=full_page)
        source = None
        if self._fx_sources:
            source = page.content()
        self.save_extras(image, comment, source)
