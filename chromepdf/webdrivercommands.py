"""
Commands for interacting with a chromedriver without requiring Selenium
"""
import base64
import json
import os
import socket
import subprocess
import urllib.request
from contextlib import contextmanager

from chromepdf.exceptions import ChromePdfException
from chromepdf.webdrivers import _get_chrome_webdriver_args


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


class NoSeleniumWebdriver:

    def __init__(self, chrome_path, chromedriver_path, **kwargs):
        self.chromedriver_path = chromedriver_path
        self.chrome_path = chrome_path
        self.chrome_args = _get_chrome_webdriver_args(**kwargs)

        # Get an available port
        self.sock = socket.socket()
        self.sock.bind(('', 0))
        self.port = self.sock.getsockname()[1]

        # Start Chromedriver
        args = [self.chromedriver_path, self.chrome_path, f'--port={self.port}']
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE)

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

    def generate_pdf(self, html, pdf_kwargs):

        # Go to data url that we will turn into the PDF
        driverurl = f'http://localhost:{self.port}/session/{self.session_id}/url'
        data = {'url': "data:text/html;charset=utf-8,"}
        output = get_chromedriver_response(driverurl, data)

        # Write the HTML for the PDF
        driverurl = f'http://localhost:{self.port}/session/{self.session_id}/execute/sync'
        html = html.replace('`', r'\`')
        script = "document.write(`{}`)".format(html)
        data = {"script": script, 'args': []}
        output = get_chromedriver_response(driverurl, data)

        return self._get_pdf_bytes(pdf_kwargs)

    def generate_pdf_url(self, url, pdf_kwargs):

        # Go to data url that we will turn into the PDF
        driverurl = f'http://localhost:{self.port}/session/{self.session_id}/url'
        data = {'url': url}
        output = get_chromedriver_response(driverurl, data)

        return self._get_pdf_bytes(pdf_kwargs)

    def _get_pdf_bytes(self, pdf_kwargs):

        # Generate PDF and bet bytes back
        driverurl = f"http://localhost:{self.port}/session/{self.session_id}/chromium/send_command_and_get_result"
        cmd = "Page.printToPDF"
        data = {'cmd': cmd, 'params': pdf_kwargs}
        output = get_chromedriver_response(driverurl, data)
        return base64.b64decode(output['value'].get('data'))

    def quit(self):

        # Exit Chrome by terminating our session
        driverurl = f'http://localhost:{self.port}/session/{self.session_id}'
        output = get_chromedriver_response(driverurl, method='DELETE')

        # Send command to kill chromedriver process
        # Then wait until it's killed, or may display ResourceError if current process ends first.
        self.proc.kill()
        self.proc.wait()

        # Unbind socket
        self.sock.close()


@contextmanager
def get_chrome_noselenium_webdriver(chrome_path, chromedriver_path, **kwargs):
    """
    Create and return a Chrome webdriver. Is a context manager, and will automatically close the driver. Usage:

    * chromedriver_path: Path to your chromedriver executable. If None, will try to find it on PATH via Selenium.
    * chrome_path: Path to your Chrome exe. If None, driver will try to find it automatically.
    kwarg-only:
    * chrome_args: List of options to pass to Chrome.

    with get_chrome_webdriver(...) as driver:
        # call commands...
    # driver is automatically closed
    """

    # contextmanager.__enter__
    try:
        driver = NoSeleniumWebdriver(chrome_path, chromedriver_path, **kwargs)
    except Exception as ex:
        if chrome_path and not os.path.exists(chrome_path):
            raise ChromePdfException(f'Could not find a chrome_path path at: {chrome_path}') from ex
        elif chromedriver_path and not os.path.exists(chromedriver_path):
            raise ChromePdfException(f'Could not find a chromedriver_path at: {chromedriver_path}') from ex
        else:
            raise ex

    yield driver

    # contextmanager.__exit__
    driver.quit()  # quits the entire driver (driver.close() only closes the current window)
