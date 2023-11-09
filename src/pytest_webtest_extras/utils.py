import base64
import html
import os
import pathlib
import pytest
import shutil
import sys
import traceback


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


def check_lists_length(report, item, fx_extras):
    """ Used to verify if the images, comments and page sources lists have coherent lenghts. """
    message = ('"images", "comments" and/or "sources" lists have incoherent lengths. '
               "Screenshots won't be logged for this test.")
    max_length = len(fx_extras.images)
    max_length = len(fx_extras.comments) if len(fx_extras.comments) > max_length else max_length
    max_length = len(fx_extras.sources) if len(fx_extras.sources) > max_length else max_length
    if (
        len(fx_extras.images) == max_length and
        len(fx_extras.comments) == max_length and
        len(fx_extras.sources) == max_length
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
def get_full_page_screenshot_chromium(driver):
    # get window size
    page_rect = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    # parameters needed for full page screenshot
    # note we are setting the width and height of the viewport to screenshot, same as the site's content size
    screenshot_config = {
        'captureBeyondViewport': True,
        'fromSurface': True,
        'format': "png",
        'clip': {
            'x': 0,
            'y': 0,
            'width': page_rect['contentSize']['width'],
            'height': page_rect['contentSize']['height'],
            'scale': 1
        },
    }
    # Dictionary with 1 key: data
    base_64_png = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
    return base64.urlsafe_b64decode(base_64_png['data'])


def save_image(report_folder, index, image):
    link = f"screenshots{os.sep}image-{index}.png"
    folder = ""
    if report_folder is not None and report_folder != '':
        folder = f"{report_folder}{os.sep}"
    filename = folder + link
    try:
        f = open(filename, 'wb')
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
        f = open(filename, 'w', encoding="utf-8")
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
    return html.escape(str(text))


def get_table_row_tag(comment, image, source, clazz="extras_log_comment"):
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
    if isinstance(comment, str):
        comment = decorate_label(comment, clazz)
    else:
        comment = ""
    if source is not None:
        source = decorate_page_source(source)
        return (
            f"<tr>"
            f"<td>{comment}</td>"
            f'<td class="extras_td"><div class="extras_td_div">{image}<br>{source}</div></td>'
            f"</tr>"
        )
    else:
        return (
            f"<tr>"
            f"<td>{comment}</td>"
            f'<td class="extras_td"><div class="extras_td_div">{image}</div></td>'
            "</tr>"
        )


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
        return f'<div class="extras_div">{image}<br>{source}</div>'
    else:
        return image


def decorate_screenshot(filename, clazz="extras_log_img"):
    """ Applies CSS style to a screenshot anchor element. """
    return f'<a href="{filename}" target="_blank"><img src ="{filename}" class="{clazz}"></a>'


def decorate_page_source(filename, clazz="extras_page_src"):
    """ Applies CSS style to a page source anchor element. """
    return f'<a href="{filename}" target="_blank" class="{clazz}">[page source]</a>'


def decorate_quote():
    """ Applies CSS style to a quotation. """
    return decorate_label('"', "extras_log_quote")


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
