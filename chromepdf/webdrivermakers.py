import base64
import json
import os
import platform
import shlex
import socket
import subprocess
import urllib
import warnings
from contextlib import contextmanager
from urllib.parse import urlparse

from chromepdf.exceptions import ChromePdfException
from chromepdf.pdfconf import clean_pdf_kwargs
from chromepdf.webdrivers import (
    _get_chrome_webdriver_args, _get_chrome_webdriver_kwargs, _get_chromedriver_environment_path, devtool_command)


@contextmanager
def get_webdriver_maker(chrome_path, chromedriver_path, use_selenium, **kwargs):

    # contextmanager.__enter__
    try:
        # If None, then use Selenium if it exists. Otherwise, fall back on no-selenium
        if use_selenium is None:
            try:
                import selenium
                use_selenium = True
            except (ImportError, ModuleNotFoundError):
                use_selenium = False
        if use_selenium:
            wrapper = SeleniumWebdriverMaker(chrome_path, chromedriver_path, **kwargs)
        else:
            wrapper = NoSeleniumWebdriverMaker(chrome_path, chromedriver_path, **kwargs)

    except Exception as ex:
        if chrome_path and not os.path.exists(chrome_path):
            raise ChromePdfException(f'Could not find a chrome_path path at: {chrome_path}') from ex
        elif chromedriver_path and not os.path.exists(chromedriver_path):
            raise ChromePdfException(f'Could not find a chromedriver_path at: {chromedriver_path}') from ex
        else:
            raise ex

    yield wrapper

    # contextmanager.__exit__
    wrapper.quit()  # quits the entire driver


class SeleniumWebdriverMaker:
    "A wrapper around a Selenium Chrome Webdriver that can generate PDFs."

    def __init__(self, chrome_path, chromedriver_path, **kwargs):
        self.chromedriver_path = chromedriver_path
        self.chrome_path = chrome_path
        self.chrome_args = _get_chrome_webdriver_args(**kwargs)

        chrome_webdriver_kwargs = _get_chrome_webdriver_kwargs(chrome_path, chromedriver_path, **kwargs)
        from selenium import webdriver
        self.driver = webdriver.Chrome(**chrome_webdriver_kwargs)

    def generate_pdf(self, html, pdf_kwargs):
        "Return the bytes of a PDF generated from HTML."

        pdf_kwargs = _clean_pdf_kwargs(pdf_kwargs)

        # we could put the html here. but data urls in Chrome are limited to 2MB.
        dataurl = "data:text/html;charset=utf-8,"
        self.driver.get(dataurl)

        # append our html. theoretically no length limit.
        html = html.replace('`', r'\`')  # escape the backtick used to indicate a multiline string in javascript
        # we do NOT need to escape any other chars (quotes, etc), including unicode
        self.driver.execute_script("document.write(`{}`)".format(html))

        return self._get_pdf_bytes(pdf_kwargs)

    def generate_pdf_url(self, url, pdf_kwargs):
        "Return the bytes of a PDF generated from a URL."

        warnings.warn("generate_pdf_url() is deprecated, use generate_pdf() instead.", DeprecationWarning)

        pdf_kwargs = _clean_pdf_kwargs(pdf_kwargs)

        # throw an early exception if we receive a string that Chrome would return a 400 error (Bad Request) if given.
        parseresult = urlparse(url)
        if not parseresult.scheme:
            raise ValueError('generate_pdf_url() requires a valid URI, beginning with file:/// or https:// or similar. '
                             'You can use: import pathlib; pathlib.Path(absolute_path).as_uri() to '
                             'convert an absolute path into such a file URI.')

        self.driver.get(url)

        return self._get_pdf_bytes(pdf_kwargs)

    def _get_pdf_bytes(self, pdf_kwargs):

        result = devtool_command(self.driver, "Page.printToPDF", pdf_kwargs)
        return base64.b64decode(result['data'])

    def quit(self):
        self.driver.quit()


class NoSeleniumWebdriverMaker:
    "A wrapper around a direct connection to a chromedriver that can generate PDFs."

    def __init__(self, chrome_path, chromedriver_path, **kwargs):
        self.chromedriver_path = chromedriver_path
        self.chrome_path = chrome_path or None

        if not self.chrome_path and not self.chromedriver_path:
            raise ChromePdfException('You must ideally provide a chrome_path, if chromedriver downloads are enabled. Or, less commonly, a chromedriver_path, if Chrome if on your PATH and your are certain that they are compatible.')
        self.chrome_args = _get_chrome_webdriver_args(**kwargs)

        # Get an available port
        self.sock = socket.socket()
        self.sock.bind(('', 0))
        self.port = self.sock.getsockname()[1]

        # Start Chromedriver
        args = [self.chromedriver_path, self.chrome_path, f'--port={self.port}']
        args = [a for a in args if a is not None]  # skip chrome_path if it is None
        is_windows = platform.system() == 'Windows'
        if not is_windows:
            # Linux needs these to be quoted in case of spaces in paths. Windows is okay though.
            args = ' '.join(shlex.quote(str(s)) for s in args)

        try:
            self.proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        except Exception as ex:
            raise OSError(f'Failed to start chromedriver process: {args}') from ex

        # Start Chrome
        driverurl = f'http://localhost:{self.port}/session'
        data = {
            "desiredCapabilities": {
                "browser": "chrome",
                "chromeOptions": {
                    "args": self.chrome_args,
                    'excludeSwitches': ['enable-logging'],  # Disables "DevTools listening" output
                }
            }
        }
        output = get_chromedriver_response(driverurl, data)
        self.session_id = output['sessionId']

    def _get_driver_command_url(self, suffix=None):
        suffix = f'/{suffix}' if suffix else ''
        return f'http://localhost:{self.port}/session/{self.session_id}{suffix}'

    def generate_pdf(self, html, pdf_kwargs):
        "Return the bytes of a PDF generated from HTML."

        pdf_kwargs = _clean_pdf_kwargs(pdf_kwargs)

        # Go to data url that we will turn into the PDF
        driverurl = self._get_driver_command_url('url')
        data = {'url': "data:text/html;charset=utf-8,"}
        output = get_chromedriver_response(driverurl, data)

        # Write the HTML for the PDF
        driverurl = self._get_driver_command_url('execute/sync')
        html = html.replace('`', r'\`')
        script = "document.write(`{}`)".format(html)
        data = {"script": script, 'args': []}
        output = get_chromedriver_response(driverurl, data)

        return self._get_pdf_bytes(pdf_kwargs)

    def generate_pdf_url(self, url, pdf_kwargs):
        "Return the bytes of a PDF generated from a URL."

        # throw an early exception if we receive a string that Chrome would return a 400 error (Bad Request) if given.
        parseresult = urlparse(url)
        if not parseresult.scheme:
            raise ValueError('generate_pdf_url() requires a valid URI, beginning with file:/// or https:// or similar. '
                             'You can use: import pathlib; pathlib.Path(absolute_path).as_uri() to '
                             'convert an absolute path into such a file URI.')

        pdf_kwargs = _clean_pdf_kwargs(pdf_kwargs)

        # Go to data url that we will turn into the PDF
        driverurl = self._get_driver_command_url('url')
        data = {'url': url}
        output = get_chromedriver_response(driverurl, data)

        return self._get_pdf_bytes(pdf_kwargs)

    def _get_pdf_bytes(self, pdf_kwargs):

        # Generate PDF and bet bytes back
        driverurl = self._get_driver_command_url('chromium/send_command_and_get_result')
        cmd = "Page.printToPDF"
        data = {'cmd': cmd, 'params': pdf_kwargs}
        output = get_chromedriver_response(driverurl, data)
        return base64.b64decode(output['value'].get('data'))

    def quit(self):

        # Exit Chrome by terminating our session
        driverurl = self._get_driver_command_url()
        output = get_chromedriver_response(driverurl, method='DELETE')

        # Send command to kill chromedriver process
        # Then wait until it's killed, or current process may display ResourceError if it ends first.
        self.proc.kill()
        self.proc.wait()

        # Unbind socket
        self.sock.close()


def _clean_pdf_kwargs(pdf_kwargs):
    """A wrapper around clean_pdf_kwargs() that handles None as well."""

    pdf_kwargs = {} if pdf_kwargs is None else pdf_kwargs
    pdf_kwargs = clean_pdf_kwargs(**pdf_kwargs)
    return pdf_kwargs


def get_chromedriver_response(url, data=None, method='POST'):
    "Send a JSON request to chromedriver, and return a JSON response."

    request = urllib.request.Request(url, method=method)
    request.add_header('Content-Type', 'application/json; charset=utf-8')
    if data is not None:
        data = json.dumps(data).encode('utf8')
    request.add_header('Content-Length', len(data) if data is not None else 0)
    with urllib.request.urlopen(request, data) as response:
        data = response.read().decode('utf8')
        data = json.loads(data)
        return data
