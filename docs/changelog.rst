=========
Changelog
=========


1.2.2
=====

**Bug fixes**

* Error when config option ``--alluredir`` is missing.
* Better handling of missing optional dependencies (**Selenium** and **Playwright**).


1.2.1
=====

**Improvement**

* Addition of auxiliary functions to format XML, JSON and YAML data from files and strings.

**Changes**

* ``screenshot_for_selenium`` method has been renamed to ``screenshot_selenium``.
* ``screenshot_for_playwright`` method has been renamed to ``screenshot_playwright``.

**Bug fix**

* **Playwright** package should be an optional dependency.


1.2.0
=====

**Improvement**

* Removal of redundant ``extras_allure`` INI option.

**Changes**

* The ``report-extras`` fixture has been renamed to ``extras``.
* Default value of ``extras_comments`` INI option is ``True``.

**Bug fix**

* Fix error message mistake.


1.1.0
=====

**Improvement**

* Replacement of deprecated code.

**Change**

* Some CSS classes have been renamed.


1.0.0
=====

**Initial release**

**Limitation**

* The **Environment** table is missing in the report when using pytest-html v3.2.0 (`#76 <https://github.com/pytest-dev/pytest-metadata/issues/76/>`_)