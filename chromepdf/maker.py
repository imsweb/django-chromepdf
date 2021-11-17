import base64
import urllib
import warnings
from urllib.parse import urlparse

from chromepdf.conf import parse_settings
from chromepdf.pdfconf import clean_pdf_kwargs
from chromepdf.webdrivers import (devtool_command,
                                  download_chromedriver_version,
                                  get_chrome_version, get_chrome_webdriver,
                                  get_printed_pdf_bytes)


class ChromePdfMaker:
    """A class used to expedite PDF creation and storing of settings state."""

    def __init__(self, **kwargs):

        # load settings, combining those from **kwargs as well as the Django settings.
        settings = parse_settings(**kwargs)
        self._chrome_path = settings['chrome_path']
        self._chromedriver_path = settings['chromedriver_path']
        self._chromedriver_downloads = settings['chromedriver_downloads']

        # download chromedriver if we have chrome, and downloads are enabled
        if self._chrome_path is not None and self._chromedriver_path is None and self._chromedriver_downloads:
            chrome_version = get_chrome_version(self._chrome_path)
            self._chromedriver_path = download_chromedriver_version(chrome_version)

        self._webdriver_kwargs = {
            'chrome_args': settings['chrome_args'],
            'chrome_path': self._chrome_path,
            'chromedriver_path': self._chromedriver_path,
        }

    def _clean_pdf_kwargs(self, pdf_kwargs):
        """A wrapper around clean_pdf_kwargs() that handles None as well."""

        pdf_kwargs = {} if pdf_kwargs is None else pdf_kwargs
        pdf_kwargs = clean_pdf_kwargs(**pdf_kwargs)
        return pdf_kwargs

    def generate_pdf(self, html, pdf_kwargs=None):
        """Generate a PDF file from an html string and return the PDF as a bytes object."""

        pdf_kwargs = self._clean_pdf_kwargs(pdf_kwargs)

        with get_chrome_webdriver(**self._webdriver_kwargs) as driver:

            # we could put the html here. but data urls in Chrome are limited to 2MB.
            dataurl = "data:text/html;charset=utf-8," + urllib.parse.quote('')
            driver.get(dataurl)

            # append our html. theoretically no length limit.
            html = html.replace('`', r'\`')  # escape the backtick used to indicate a multiline string in javascript
            # we do NOT need to escape any other chars (quotes, etc), including unicode
            driver.execute_script("document.write(`{}`)".format(html))

            outbytes = get_printed_pdf_bytes(driver, pdf_kwargs)

        return outbytes

    def generate_pdf_url(self, url, pdf_kwargs=None):
        """Generate a PDF file from a url (such as a file:/// url) and return the PDF as a bytes object."""

        warnings.warn("ChromePdfMaker.generate_pdf_url() is deprecated, use generate_pdf() instead.", DeprecationWarning)

        # throw an early exception if we receive a string that Chrome would return a 400 error (Bad Request) if given.
        parseresult = urlparse(url)
        if not parseresult.scheme:
            raise ValueError('generate_pdf_url() requires a valid URI, beginning with file:/// or https:// or similar. '
                             'You can use: import pathlib; pathlib.Path(absolute_path).as_uri() to '
                             'convert an absolute path into such a file URI.')

        pdf_kwargs = self._clean_pdf_kwargs(pdf_kwargs)

        with get_chrome_webdriver(**self._webdriver_kwargs) as driver:
            driver.get(url)
            outbytes = get_printed_pdf_bytes(driver, pdf_kwargs)

        return outbytes
