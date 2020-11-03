# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1](https://github.com/imsweb/django-chromepdf/tree/1.1.1) - 2020-11-03

### Fixed

- Lengths passed as a `Decimal` type will now be converted to `float` rather than raising an exception due to not being JSON-serializable.

### Added

- Compatibility with Selenium 4. Selenium 4 now uses proxy environment variables unless it is explicitly told not to. ChromePDF now tells it not to. ChromePDF still requires Selenium 3 as a requirement. The actual switch to Selenium 4 will occur in a future release.
- URI schema check for `generate_pdf_url()`. This function will now raise a `ValueError` for invalid schemas rather than passing Chrome a URI that it cannot handle.
- Additional unit tests, especially for unit conversions and stress testing of large PDFs.

## 1.1.0 - 2020-10-01

### Added

- Initial Release

