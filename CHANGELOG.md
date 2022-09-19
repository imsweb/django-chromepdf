# Changelog

All notable changes to this project will be documented in this file.


## [1.4.0](https://github.com/imsweb/django-chromepdf/tree/1.4.0) - 2022-09-20

**Added**

- Added a command-line API for generating PDFs without having to write Python code. See the new section in the readme for more information.


## [1.3.2](https://github.com/imsweb/django-chromepdf/tree/1.3.2) - 2022-06-06

**Fixed**

- Fixed an issue where multithreading and/or multi-user simultaneous PDF generation could cause stalling due to attempts to write to the same files. Chrome is now launched with the `--incognito` and `--disable-crash-reporter` args to disable creation of files that caused these conflicts.


## [1.3.1](https://github.com/imsweb/django-chromepdf/tree/1.3.1) - 2022-03-04

**Fixed**

- Fixed file permission issues in Chrome 99+ by storing user data and crash dumps into local folder instead of global folder.
- Fixed a `ResourceWarning` due to webdriver connections not properly being closed.
- Fixed a `DeprecationWarning` raised by Selenium 4 changing the way a chromedriver is passed, from `executable_path` to `Service` objects.


## [1.3.0](https://github.com/imsweb/django-chromepdf/tree/1.3.0) - 2021-12-06

**Changed**

- Selenium 4 is now preferred; Selenium 3 is still supported (dependency changed from `selenium<4` to `selenium<5,>=3`)
- Minimum-supported Django version is now 3.2 (Django is not a required dependency but can be used for global configs; using prior versions may work but is not guaranteed)

**Added**

- Added support for downloading Apple M1 ARM-compatible chromedrivers when used on an Apple M1 device.


## [1.2.1](https://github.com/imsweb/django-chromepdf/tree/1.2.1) - 2021-03-04

### Fixed

- Fixed a bug where the chromedriver download path was not being used if a chromedriver was just downloaded. This bug was introduced in 1.2.0. Earlier versions are not affected.


## [1.2.0](https://github.com/imsweb/django-chromepdf/tree/1.2.0) - 2021-02-04

**Added**

- Added a `CHROME_ARGS` Django setting (and `chrome_args` function parameter to `generate_pdf()`) which accepts a list of string parameters to pass to Google Chrome when calling it.
- Added compatibility with MacOS.

**Changed**

- `pdf_kwargs` is no longer a required parameter for`ChromePdfMaker.generate_pdf()`, similar to the shortcut function, `generate_pdf()`


## [1.1.1](https://github.com/imsweb/django-chromepdf/tree/1.1.1) - 2020-11-03

**Fixed**

- Lengths passed as a `Decimal` type will now be converted to `float` rather than raising an exception due to not being JSON-serializable.

**Added**

- Added compatibility with Selenium 4. Selenium 4 now uses proxy environment variables unless it is explicitly told not to. ChromePDF now tells it not to. ChromePDF still requires Selenium 3 as a requirement. The actual switch to Selenium 4 will occur in a future release.
- Added URI schema check for `generate_pdf_url()`. This function will now raise a `ValueError` for invalid schemas rather than passing Chrome a URI that it cannot handle.
- Added additional unit tests, especially for unit conversions and stress testing of large PDFs.


## 1.1.0 - 2020-10-01

**Added**

- First Public Release

