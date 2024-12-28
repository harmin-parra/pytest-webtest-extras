import os
import pytest
from . import utils
from .extras import Extras


#
# Definition of test options
#
def pytest_addoption(parser):
    parser.addini(
        "extras_screenshots",
        type="string",
        default="all",
        help="The screenshots to include in the report. Accepted values: all, last, none."
    )
    parser.addini(
        "extras_comments",
        type="bool",
        default=True,
        help="Whether to include comments."
    )
    parser.addini(
        "extras_sources",
        type="bool",
        default=False,
        help="Whether to include webpage sources."
    )
    parser.addini(
        "extras_description_tag",
        type="string",
        default="h2",
        help="HTML tag for the test description. Accepted values: h1, h2, h3, p or pre.",
    )


#
# Read test parameters
#
@pytest.fixture(scope='session')
def screenshots(request):
    value = request.config.getini("extras_screenshots")
    if value in ("all", "last", "none"):
        return value
    else:
        return "all"


@pytest.fixture(scope='session')
def report_folder(request):
    """ The folder storing the pytest-html report """
    htmlpath = request.config.getoption("--html")
    return utils.get_folder(htmlpath)


@pytest.fixture(scope='session')
def report_allure(request):
    """ Whether the allure-pytest plugin is being used """
    return request.config.getoption("--alluredir", default=None) is not None


@pytest.fixture(scope='session')
def report_css(request):
    """ The filepath of the CSS to include in the report. """
    return request.config.getoption("--css")


@pytest.fixture(scope='session')
def description_tag(request):
    """ The HTML tag for the description of each test. """
    tag = request.config.getini("extras_description_tag")
    return tag if tag in ("h1", "h2", "h3", "p", "pre") else "h2"


@pytest.fixture(scope='session')
def comments(request):
    """ Whether to include the gathered comments in the report. """
    return request.config.getini("extras_comments")


@pytest.fixture(scope='session')
def sources(request):
    """ Whether to include webpage sources in the report. """
    return request.config.getini("extras_sources")


@pytest.fixture(scope='session')
def check_options(request, report_folder):
    """ Verifies preconditions before using this plugin. """
    utils.check_html_option(report_folder)
    utils.create_assets(report_folder)


#
# Test fixture
#
@pytest.fixture(scope='function')
def report(request, report_folder, screenshots, comments, sources, report_allure, check_options):
    return Extras(report_folder, screenshots, comments, sources, report_allure)


#
# Hookers
#
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    import warnings
    warnings.warn("\n\npytest-webtest-extras plugin is deprecated.\nPlease use 'pytest-report-extras' plugin instead (https://pytest-report-extras.readthedocs.io/stable/)\n", DeprecationWarning)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """ Override report generation. """
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, 'extras', [])

    # Is the test item using the 'report' fixtures?
    if not ("request" in item.funcargs and "report" in item.funcargs):
        return

    if report.when == 'call':
        # Get test fixture values
        feature_request = item.funcargs['request']
        fx_report = feature_request.getfixturevalue("report")
        fx_description_tag = feature_request.getfixturevalue("description_tag")
        fx_screenshots = feature_request.getfixturevalue("screenshots")
        fx_comments = feature_request.getfixturevalue("comments")
        images = fx_report.images
        sources = fx_report.sources
        comments = fx_report.comments

        # Append test description and execution exception trace, if any.
        description = item.function.__doc__ if hasattr(item, 'function') else None
        utils.append_header(call, report, extras, pytest_html, description, fx_description_tag)

        if fx_screenshots == "none" or len(images) == 0:
            return

        if not utils.check_lists_length(report, fx_report):
            return

        # Generate HTML code for the extras to be added in the report
        links = ""  # Used when logging without comments
        rows = ""   # Used when logging with comments
        if fx_screenshots == "all":
            if not fx_comments:
                for i in range(len(images)):
                    links += utils.decorate_anchors(images[i], sources[i])
            else:
                for i in range(len(images)):
                    rows += utils.get_table_row_tag(comments[i], images[i], sources[i])
        else:  # fx_screenshots == "last"
            if len(images) > 0:
                if not fx_comments:
                    links = utils.decorate_anchors(images[-1], sources[-1])
                else:
                    rows += utils.get_table_row_tag(comments[-1], images[-1], sources[-1])

        # Add horizontal line between the header and the comments/screenshots
        if len(extras) > 0 and len(links) + len(rows) > 0:
            extras.append(pytest_html.extras.html(f'<hr class="extras_separator">'))

        # Append extras
        if links != "":
            extras.append(pytest_html.extras.html(links))
        if rows != "":
            rows = (
                '<table style="width: 100%;">'
                + rows +
                "</table>"
            )
            extras.append(pytest_html.extras.html(rows))
        report.extras = extras

        # Log error message if there was a screenshot gathering failure
        if fx_screenshots != 'none':
            for image in images:
                if image == f"screenshots{os.sep}error.png":
                    message = "Failure gathering screenshot(s)"
                    utils.log_error_message(report, message)
                    break
