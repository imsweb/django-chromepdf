import os

from chromepdf.conf import parse_settings
from chromepdf.webdrivermakers import get_webdriver_maker
from chromepdf.webdrivers import _get_chromesession_temp_dir, download_chromedriver_version, get_chrome_version


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

        # download chromedriver if we have chrome, and downloads are enabled
        if self._chrome_path is not None and self._chromedriver_path is None and self._chromedriver_downloads:
            chrome_version = get_chrome_version(self._chrome_path, as_tuple=False)
            self._chromedriver_path = download_chromedriver_version(chrome_version)

        self._webdriver_kwargs = {
            'chrome_args': settings['chrome_args'],
            'chrome_path': self._chrome_path,
            'chromedriver_path': self._chromedriver_path,
            '_chromesession_temp_dir': self._chromesession_temp_dir,
            'use_selenium': self._use_selenium,
        }

    def generate_pdf(self, html, pdf_kwargs=None):
        """Generate a PDF file from an html string and return the PDF as a bytes object."""

        with get_webdriver_maker(**self._webdriver_kwargs) as wrapper:
            return wrapper.generate_pdf(html, pdf_kwargs)

    def generate_pdf_url(self, url, pdf_kwargs=None):
        """Generate a PDF file from a url (such as a file:/// url) and return the PDF as a bytes object."""

        with get_webdriver_maker(**self._webdriver_kwargs) as wrapper:
            return wrapper.generate_pdf_url(url, pdf_kwargs)
