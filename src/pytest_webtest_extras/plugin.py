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
def check_options(request, report_folder):
    utils.check_html_option(report_folder)
    utils.create_assets(report_folder)


#
# Test fixture
#
@pytest.fixture(scope='function')
def webtest_extras(request, report_folder, screenshots, comments, sources, check_options):
    return Extras(report_folder, screenshots, comments, sources)


#
# Hookers
#
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """ Override report generation. """
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, 'extras', [])

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
        if not ("request" in item.funcargs and "webtest_extras" in item.funcargs):
            return
        feature_request = item.funcargs['request']

        # Get test fixture values
        fx_extras = feature_request.getfixturevalue("webtest_extras")
        fx_description_tag = feature_request.getfixturevalue("description_tag")
        fx_screenshots = feature_request.getfixturevalue("screenshots")
        fx_comments = feature_request.getfixturevalue("comments")

        # Append test description and execution exception trace, if any.
        utils.append_header(call, report, extras, pytest_html, description, fx_description_tag)

        if fx_screenshots == "none" or len(fx_extras.images) == 0:
            report.extras = extras
            return

        if not utils.check_lists_length(report, item, fx_extras):
            return

        links = ""
        rows = ""
        if fx_screenshots == "all":
            if not fx_comments:
                for i in range(len(fx_extras.images)):
                    links += utils.decorate_anchors(fx_extras.images[i], fx_extras.sources[i])
            else:
                for i in range(len(fx_extras.images)):
                    rows += utils.get_table_row_tag(fx_extras.comments[i], fx_extras.images[i], fx_extras.sources[i])
        else:  # fx_screenshots == "last"
            if len(fx_extras.images) > 0:
                if not fx_comments:
                    links = utils.decorate_anchors(fx_extras.images[-1], fx_extras.sources[-1])
                else:
                    rows += utils.get_table_row_tag(fx_extras.comments[-1], fx_extras.images[-1], fx_extras.sources[-1])

        # Add horizontal line between the header and the comments/screenshots
        if len(extras) > 0 and len(links) + len(rows) > 0:
            extras.append(pytest_html.extras.html(f'<hr class="selenium_separator">'))

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
