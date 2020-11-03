# Changelog

All notable changes to this project will be documented in this file.

## 1.1.1 - Unreleased

### Fixed

- Lengths passed as a `Decimal` type will now be converted to `float` rather than raising an exception due to not being JSON-serializable.

### Added

- Compatibility with Selenium 4. Selenium 4 now uses proxy environment variables unless it is explicitly told not to. ChromePDF now tells it not to.
- URI schema check for `generate_pdf_url()`. This function will now raise a `ValueError` for invalid schemas rather than passing Chrome a URI that it cannot handle.
- Additional unit tests, especially for unit conversions and stress testing of large PDFs.

## 1.1.0 - 2020-10-01

### Added

- Initial Release

