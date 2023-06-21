import os
from urllib.parse import urlparse

from chromepdf.conf import parse_settings
from chromepdf.webdrivermakers import (
    NoSeleniumWebdriverMaker, SeleniumWebdriverMaker, get_webdriver_maker, get_webdriver_maker_class,
    is_selenium_installed)
from chromepdf.webdrivers import (
    _get_chromesession_temp_dir, download_chromedriver_version, find_chrome, get_chrome_version)


class ChromePdfMaker:
    """A class used to expedite PDF creation and storing of settings state."""

    def __init__(self, **kwargs):

        # load settings, combining those from **kwargs as well as the Django settings.
        settings = parse_settings(**kwargs)
        self._chrome_path = settings['chrome_path']
        self._chromedriver_path = settings['chromedriver_path']
        self._chromedriver_downloads = settings['chromedriver_downloads']
        self._chromesession_temp_dir = _get_chromesession_temp_dir()

        self._use_selenium = settings['use_selenium']

        os.makedirs(self._chromesession_temp_dir, exist_ok=True)

        self._clazz = get_webdriver_maker_class(self._use_selenium)
        if self._use_selenium is None:
            self._use_selenium = is_selenium_installed()
            if self._use_selenium:
                pass
            else:
                # Mimic Selenium's ability to identify Chrome if it's on the PATH.
                # This is done here by overriding the parameter given by the user.
                # Which isn't ideal. But it is preferable to the webdriver makers needing to deal with chromedriver
                # versioning and downloads. And it doesn't break backwards-compatibility since
                # this only occurs if Selenium is not present.
                if self._chrome_path is None:
                    self._chrome_path = find_chrome()

        # download chromedriver if we have chrome, and downloads are enabled
        if self._chrome_path is not None and self._chromedriver_path is None and self._chromedriver_downloads:
            chrome_version = get_chrome_version(self._chrome_path, as_tuple=False)
            self._chromedriver_path = download_chromedriver_version(chrome_version)

        self._webdriver_kwargs = {
            'chrome_args': settings['chrome_args'],
            'chrome_path': self._chrome_path,
            'chromedriver_path': self._chromedriver_path,
            '_chromesession_temp_dir': self._chromesession_temp_dir,
        }

    def generate_pdf(self, html, pdf_kwargs=None):
        """Generate a PDF file from an html string and return the PDF as a bytes object."""

        with get_webdriver_maker(self._clazz, **self._webdriver_kwargs) as wrapper:
            return wrapper.generate_pdf(html, pdf_kwargs)

    def generate_pdf_url(self, url, pdf_kwargs=None):
        """Generate a PDF file from a url (such as a file:/// url) and return the PDF as a bytes object."""

        # throw an early exception if we receive a string that Chrome would return a 400 error (Bad Request) if given.
        parseresult = urlparse(url)
        if not parseresult.scheme:
            raise ValueError('generate_pdf_url() requires a valid URI, beginning with file:/// or https:// or similar. '
                             'You can use: import pathlib; pathlib.Path(absolute_path).as_uri() to '
                             'convert an absolute path into such a file URI.')

        with get_webdriver_maker(self._clazz, **self._webdriver_kwargs) as wrapper:
            return wrapper.generate_pdf_url(url, pdf_kwargs)
