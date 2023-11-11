import importlib
import os
import pytest
import re
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
        default=False,
        help="Whether to include comments."
    )
    parser.addini(
        "extras_sources",
        type="bool",
        default=False,
        help="Whether to include webpage sources."
    )
    parser.addini(
        "extras_allure",
        type="bool",
        default=True,
        help="Whether to attach extras to allure."
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
    htmlpath = request.config.getoption("--html")
    return utils.get_folder(htmlpath)


@pytest.fixture(scope='session')
def report_css(request):
    return request.config.getoption("--css")


@pytest.fixture(scope='session')
def description_tag(request):
    tag = request.config.getini("extras_description_tag")
    return tag if tag in ("h1", "h2", "h3", "p", "pre") else "h2"


@pytest.fixture(scope='session')
def comments(request):
    return request.config.getini("extras_comments")


@pytest.fixture(scope='session')
def sources(request):
    return request.config.getini("extras_sources")


@pytest.fixture(scope='session')
def include_allure(request):
    return request.config.getini("extras_allure")


@pytest.fixture(scope='session')
def check_options(request, report_folder):
    utils.check_html_option(report_folder)
    utils.create_assets(report_folder)


#
# Test fixture
#
@pytest.fixture(scope='function')
def report_extras(request, report_folder, screenshots, comments, sources, check_options, include_allure):
    return Extras(report_folder, screenshots, comments, sources, include_allure)


#
# Hookers
#
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """ Override report generation. """
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, 'extra', [])

    # Let's deal with the HTML report
    if report.when == 'call':
        # Get function/method description
        pkg = item.location[0].replace(os.sep, '.')[:-3]
        index = pkg.rfind('.')
        module = importlib.import_module(package=pkg[:index], name=pkg[index + 1:])
        # Is the called test a function ?
        match_cls = re.search(r"^[^\[]*\.", item.location[2])
        if match_cls is None:
            func = getattr(module, item.originalname)
        else:
            cls = getattr(module, match_cls[0][:-1])
            func = getattr(cls, item.originalname)
        description = getattr(func, "__doc__")

        # Is the test item using the 'extras' fixtures?
        if not ("request" in item.funcargs and "report_extras" in item.funcargs):
            return
        feature_request = item.funcargs['request']

        # Get test fixture values
        report_extras = feature_request.getfixturevalue("report_extras")
        description_tag = feature_request.getfixturevalue("description_tag")
        screenshots = feature_request.getfixturevalue("screenshots")
        log_comments = feature_request.getfixturevalue("comments")
        include_allure = feature_request.getfixturevalue("include_allure")
        images = report_extras.images
        sources = report_extras.sources
        comments = report_extras.comments

        # Append test description and execution exception trace, if any.
        utils.append_header(call, report, extras, pytest_html, description, description_tag)

        if screenshots == "none" or len(images) == 0:
            report.extra = extras
            return

        if not utils.check_lists_length(report, item, report_extras):
            report.extra = extras
            return

        # Generate HTML code for the extras to be added in the report
        links = ""  # Used when logging without comments
        rows = ""   # Used when logging with comments
        if screenshots == "all":
            if not log_comments:
                for i in range(len(images)):
                    links += utils.decorate_anchors(images[i], sources[i])
            else:
                for i in range(len(images)):
                    rows += utils.get_table_row_tag(comments[i], images[i], sources[i])
        else:  # screenshots == "last"
            if len(images) > 0:
                if not log_comments:
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
        report.extra = extras

        # Check if there was a screenshot gathering failure
        if screenshots != 'none':
            for image in images:
                if image == f"screenshots{os.sep}error.png":
                    message = "Failure gathering screenshot(s)"
                    utils.log_error_message(report, item, message)
                    break
