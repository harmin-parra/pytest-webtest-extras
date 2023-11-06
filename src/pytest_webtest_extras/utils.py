import os
import pathlib
import pytest
import shutil
import sys
import traceback
from .extras import Extras 


#
# Auxiliary functions to check options and fixtures
#
def check_html_option(htmlpath):
    if htmlpath is None:
        msg = ("It seems you are using pytest-selenium-auto plugin.\n"
               "pytest-html plugin is required.\n"
               "'--html' option is missing.\n")
        print(msg, file=sys.stderr)
        sys.exit(pytest.ExitCode.USAGE_ERROR)


def getini(config, name):
    """ Workaround for bug https://github.com/pytest-dev/pytest/issues/11282 """
    value = config.getini(name)
    if not isinstance(value, str):
        value = None
    return value


def get_folder(filepath):
    """
    Returns the folder of a filepath.
    
    Args:
        filepath (str): The filepath.
    """
    folder = None
    if filepath is not None:
        folder = os.path.dirname(filepath)
    return folder


def check_lists_length(report, item, fx_extras: Extras):
    """ Used to verify if the images, comments and page sources lists have coherent lenghts. """
    message = ('Lists "images", "comments" and "sources" have incoherent lengths. '
               "Screenshots won't be logged for this test.")
    max_length = len(fx_extras.images)
    max_length = len(fx_extras.comments) if len(fx_extras.comments) > max_length else max_length
    max_length = len(fx_extras.sources) if len(fx_extras.sources) > max_length else max_length
    if len(fx_extras.images) == max_length:
        if (
            (len(fx_extras.comments) == max_length or len(fx_extras.comments) == 0) and
            (len(fx_extras.sources) == max_length or len(fx_extras.sources) == 0)
        ):
            return True
    log_error_message(report, item, message)
    return False


def create_assets(report_folder):
    """ Recreate screenshots, page sources and log folders. """
    # Recreate screenshots_folder
    folder = ""
    if report_folder is not None and report_folder != '':
        folder = f"{report_folder}{os.sep}"
    # Create page sources folder
    shutil.rmtree(f"{folder}sources", ignore_errors=True)
    pathlib.Path(f"{folder}sources").mkdir(parents=True)
    # Create screenshots folder
    shutil.rmtree(f"{folder}screenshots", ignore_errors=True)
    pathlib.Path(f"{folder}screenshots").mkdir(parents=True)
    # Copy error.png to screenshots folder
    resources_path = pathlib.Path(__file__).parent.joinpath("resources")
    error_img = pathlib.Path(resources_path, "error.png")
    shutil.copy(str(error_img), f"{folder}screenshots")


#
# Persistence functions
#
def save_screenshot_selenium(report_folder, index, driver):
    """
    Save a screenshot in 'screenshots' folder under the specified folder.
    
    Returns:
        str: The filename for the anchor link.
    """
    link = f"screenshots{os.sep}image-{index}.png"
    folder = ""
    if report_folder is not None and report_folder != '':
        folder = f"{report_folder}{os.sep}"
    filename = folder + link
    try:
        if hasattr(driver, "save_full_page_screenshot"):
            driver.save_full_page_screenshot(filename)
        else:
            driver.save_screenshot(filename)
    except Exception as e:
        trace = traceback.format_exc()
        link = f"screenshots{os.sep}error.png"
        print(f"{str(e)}\n\n{trace}", file=sys.stderr)
    finally:
        return link


def save_image(report_folder, index, image):
    link = f"screenshots{os.sep}image-{index}.png"
    folder = ""
    if report_folder is not None and report_folder != '':
        folder = f"{report_folder}{os.sep}"
    filename = folder + link
    import base64
    try:
        f = open(filename, 'wb')
        #f.write(base64.decodebytes(image))
        f.write(image)
        f.close()
    except Exception as e:
        trace = traceback.format_exc()
        link = f"screenshots{os.sep}error.png"
        print(f"{str(e)}\n\n{trace}", file=sys.stderr)
    finally:
        return link


def save_source(report_folder, index, source):
    link = f"sources{os.sep}page-{index}.txt"
    folder = ""
    if report_folder is not None and report_folder != '':
        folder = f"{report_folder}{os.sep}"
    filename = folder + link
    try:
        f = open(filename, 'w')
        f.write(source)
        f.close()
    except Exception as e:
        trace = traceback.format_exc()
        link = None
        print(f"{str(e)}\n\n{trace}", file=sys.stderr)
    finally:
        return link


def save_page_source_selenium(report_folder, index, driver):
    """
    Saves the HTML page source with TXT extension
    in 'sources' folder under the specified folder.
    
    Returns:
        str: The filename for the anchor link.
    """
    link = f"sources{os.sep}page-{index}.txt"
    folder = ""
    if report_folder is not None and report_folder != '':
        folder = f"{report_folder}{os.sep}"
    filename = folder + link
    try:
        source = driver.page_source
        # document_root = html.fromstring(source)
        # source = etree.tostring(document_root, encoding='unicode', pretty_print=True)
        f = open(filename, 'w')
        f.write(source)
        f.close()
    except Exception as e:
        trace = traceback.format_exc()
        link = None
        print(f"{str(e)}\n\n{trace}", file=sys.stderr)
    finally:
        return link


#
# Auxiliary functions for the report generation
#
def append_header(call, report, extras, pytest_html,
                  description, description_tag):
    """
    Appends the description and the test execution exception trace, if any, to a test report.
    
    Args:
        description (str): The test file docstring.
        
        description_tag (str): The HTML tag to use.
    """
    # Append description
    if description is not None:
        description = escape_html(description).strip().replace('\n', "<br>")
        extras.append(pytest_html.extras.html(f"<{description_tag}>{description}</{description_tag}>"))

    # Catch explicit pytest.fail and pytest.skip calls
    if (
        hasattr(call, 'excinfo') and
        call.excinfo is not None and
        call.excinfo.typename in ('Failed', 'Skipped') and
        hasattr(call.excinfo, "value") and
        hasattr(call.excinfo.value, "msg")
    ):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f"<span style='color:black;'>{escape_html(call.excinfo.typename)}</span>"
            f" reason = {escape_html(call.excinfo.value.msg)}"
            "</pre>"
            )
        )
    # Catch XFailed tests
    if report.skipped and hasattr(report, 'wasxfail'):
        extras.append(pytest_html.extras.html(
            "<pre>"
            "<span style='color:black;'>XFailed</span>"
            f" reason = {escape_html(report.wasxfail)}"
            "</pre>"
            )
        )
    # Catch XPassed tests
    if report.passed and hasattr(report, 'wasxfail'):
        extras.append(pytest_html.extras.html(
            "<pre>"
            "<span style='color:black;'>XPassed</span>"
            f" reason = {escape_html(report.wasxfail)}"
            "</pre>"
            )
        )
    # Catch explicit pytest.xfail calls and runtime exceptions in failed tests
    if (
        hasattr(call, 'excinfo') and
        call.excinfo is not None and
        call.excinfo.typename not in ('Failed', 'Skipped') and
        hasattr(call.excinfo, '_excinfo') and
        call.excinfo._excinfo is not None and
        isinstance(call.excinfo._excinfo, tuple) and
        len(call.excinfo._excinfo) > 1
    ):
        extras.append(pytest_html.extras.html(
            "<pre>"
            f"<span style='color:black;'>{escape_html(call.excinfo.typename)}</span>"
            f" {escape_html(call.excinfo._excinfo[1])}"
            "</pre>"
            )
        )
    # extras.append(pytest_html.extras.html("<br>"))


def escape_html(text):
    """ Escapes the '<' and '>' characters. """
    return str(text).replace('<', "&lt;").replace('>', "&gt;")


def get_table_row_tag(comment, image, source, clazz="selenium_log_comment"):
    """
    Returns the HTML table row of a test step.
    
    Args:
        comment (str): The comment of the test step.
        
        image (str): The screenshot anchor element.
        
        source (str): The page source anchor element.
        
        clazz (str): The CSS class to apply.
    
    Returns:
        str: The <tr> element.
    """
    image = decorate_screenshot(image)
    if isinstance(comment, dict):
        comment = decorate_description(comment)
    elif isinstance(comment, str):
        comment = decorate_label(comment, clazz)
    else:
        comment = ""
    if source is not None:
        source = decorate_page_source(source)
        return (
            f"<tr>"
            f"<td>{comment}</td>"
            f'<td class="selenium_td"><div class="selenium_td_div">{image}<br>{source}</div></td>'
            f"</tr>"
        )
    else:
        return (
            f"<tr>"
            f"<td>{comment}</td>"
            f'<td class="selenium_td"><div class="selenium_td_div">{image}</div></td>'
            "</tr>"
        )


def decorate_description(description):
    """ Applies CSS style to a test step description. """
    if description is None:
        return ""

    if 'comment' not in description:
        description['comment'] = None
    if 'url' not in description:
        description['url'] = None
    if 'value' not in description:
        description['value'] = None
    if 'locator' not in description:
        description['locator'] = None
    if 'attributes' not in description:
        description['attributes'] = None

    if description['comment'] is not None:
        return decorate_label(description['comment'], "selenium_log_comment")
    label = decorate_label(description['action'], "selenium_log_action")
    if description['url'] is not None:
        label += " " + decorate_label(description['url'], "selenium_log_target")
    else:
        if description['value'] is not None:
            label += " " + decorate_quote() + description['value'] + decorate_quote()
        if description['locator'] is not None or description['attributes'] is not None:
            label += "<br/><br>"
            if description['locator'] is not None:
                locator = description['locator'].replace('"', decorate_quote())
                label += "Locator: " + decorate_label(locator, "selenium_log_target") + "<br/><br>"
            if description['attributes'] is not None:
                label += "Attributes: " + decorate_label(description['attributes'], "selenium_log_target")
    return decorate_label(label, "selenium_log_description")


def decorate_label(label, clazz):
    """
    Applies a CSS style to a text.
    
    Args:
        label (str): The text to decorate.
        
        clazz (str): The CSS class to apply.
    
    Returns:
        The <span> element. 
    """
    return f'<span class="{clazz}">{label}</span>'


def decorate_anchors(image, source):
    """ Applies CSS style to a screenshot and page source anchor elements. """
    image = decorate_screenshot(image)
    if source is not None:
        source = decorate_page_source(source)
        return f'<div class="selenium_div">{image}<br>{source}</div>'
    else:
        return image


def decorate_screenshot(filename, clazz="selenium_log_img"):
    """ Applies CSS style to a screenshot anchor element. """
    return f'<a href="{filename}" target="_blank"><img src ="{filename}" class="{clazz}"></a>'


def decorate_page_source(filename, clazz="selenium_page_src"):
    """ Applies CSS style to a page source anchor element. """
    return f'<a href="{filename}" target="_blank" class="{clazz}">[page source]</a>'


def decorate_quote():
    """ Applies CSS style to a quotation. """
    return decorate_label('"', "selenium_log_quote")


def log_error_message(report, item, message):
    """ Appends error message in stderr section of a test report. """
    try:
        i = -1
        for x in range(len(report.sections)):
            if "stderr call" in report.sections[x][0]:
                i = x
                break
        if i != -1:
            report.sections[i] = (
                report.sections[i][0],
                report.sections[i][1] + '\n' + message + '\n'
            )
        else:
            report.sections.append(('Captured stderr call', message))
    except:
        pass
