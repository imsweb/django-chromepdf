import getpass
import io
import json
import os
import platform
import shutil
import subprocess
import zipfile
from contextlib import contextmanager
from subprocess import PIPE
from urllib import request as urllib_request

import selenium
from chromepdf.exceptions import ChromePdfException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

_IS_SELENIUM_3 = selenium.__version__.split('.')[0] == '3'


def get_chrome_version(path):
    """
    Return a 4-tuple containing the version number of the Chrome binary exe, EG for Chrome 85: (85,0,4183,121)
    raise ChromePdfException otherwise (EG if path not found)
    """

    is_windows = (platform.system() == 'Windows')

    if is_windows:
        cmd = f'(Get-Item "{path}").VersionInfo'
        proc = subprocess.run(['powershell', cmd], stdout=PIPE, stderr=PIPE)
        # NOTE: "chrome.exe --version" does NOT work on windows. This is one workaround.
        # https://bugs.chromium.org/p/chromium/issues/detail?id=158372
        #
        # this will output a table like so. In this case, we want to grab the "85.0.4183.121"
        # ProductVersion   FileVersion      FileName
        # --------------   -----------      --------
        # 85.0.4183.121    85.0.4183.121    C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
        lines = [l.strip() for l in proc.stdout.decode('utf8').split('\n') if l.strip()]
        for l in lines:
            if l[0].isdigit():
                version = l.split()[0]
                return tuple(int(i) for i in version.split('.'))
    else:  # linux, mac can both just use "--version"
        proc = subprocess.run([path, '--version'], stdout=PIPE, stderr=PIPE)
        version_stdout = proc.stdout.decode('utf8').strip()  # returns, eg, "Google Chrome 85.0.4183.121"
        version = [i for i in version_stdout.split() if i[0].isdigit()][0]
        return tuple(int(i) for i in version.split('.'))

    raise ChromePdfException(f'Could not determine version of Chrome located at: f{path}')


def _get_chromedriver_environment_path():
    """
    Return full path of chromedriver on PATH, if it exists. Otherwise, return None.
    This can be used to determine if Selenium can find the chromedriver without having to specify its location.
    """

    is_windows = (platform.system() == 'Windows')
    filename = 'chromedriver.exe' if is_windows else 'chromedriver'
    return shutil.which(filename)


def _get_chromedriver_download_path(major_version):
    """Return a path to put/find a chromedriver file, if ChromePDF should/did download it."""

    assert isinstance(major_version, int)

    is_windows = (platform.system() == 'Windows')
    chromedrivers_dir = os.path.join(os.path.dirname(__file__), 'chromedrivers')
    chromedriver_path = os.path.join(chromedrivers_dir, f'chromedriver_{major_version}')
    if is_windows:  # windows requires an extension or it won't run.
        chromedriver_path += '.exe'
    else:  # linux, mac = no extension
        pass
    return chromedriver_path


def download_chromedriver_version(version, force=False):
    """
    Download a chromedriver executable for the Chrome version specified, if not already downloaded or force=True.
    Return the path of the existing (or newly downloaded) chromedriver executable.

    See https://chromedriver.chromium.org/downloads/version-selection
    for download url api

    Arguments:
    * version: A 4-int tuple version as returned by get_chrome_version(), such as: (85,0,4183,121)
    * force: If True, will force a download, even if a driver for that version is already saved.
    """

    assert isinstance(version, tuple) and (isinstance(i, int) for i in version), f'{version} must be a 4-tuple of ints.'

    version_major = version[0]

    # Return the existing path if it exists and we're not forcing a new download.
    chromedriver_download_path = _get_chromedriver_download_path(version_major)
    if os.path.exists(chromedriver_download_path) and not force:
        return chromedriver_download_path

    # Google's API for the latest release takes only the first 3 parts of the version
    version_first3parts = '.'.join(str(i) for i in version[:3])  # EG, "85.0.4183"

    # This url returns a 4-part version string of the latest compatible chromedriver for your Chrome version.
    # This might be DIFFERENT than the version of your Chrome executable.
    url = f'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version_first3parts}'
    with urllib_request.urlopen(url) as f:
        contents = f.read()
    latest_version_str = contents.decode('utf8')  # EG "85.0.4183.87"

    # Get the name of the chromedriver zip download file for our particular OS+Processor
    is_windows = (platform.system() == 'Windows')
    is_mac = (platform.system() == 'Darwin')
    is_mac_m1 = (is_mac and platform.processor() == 'arm')
    os_plus_numbits = 'win32' if is_windows else 'mac64_m1' if is_mac_m1 else 'mac64' if is_mac else 'linux64'
    filename = f'chromedriver_{os_plus_numbits}.zip'

    # Download the zip file
    url2 = f'https://chromedriver.storage.googleapis.com/{latest_version_str}/{filename}'
    with urllib_request.urlopen(url2) as f:
        zip_bytes = f.read()

    # open the zip file, find the chromedriver, and save it to the specified path.
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    for name in zf.namelist():
        if 'chromedriver' in name:
            with zf.open(name) as chromedriver_file:
                with open(chromedriver_download_path, 'wb') as f:
                    f.write(chromedriver_file.read())
                    os.chmod(chromedriver_download_path, 0o764)  # grant execute permission
                    return chromedriver_download_path

    raise ChromePdfException('Failed to download the chromedriver file.')


@contextmanager
def get_chrome_webdriver(chrome_path, chromedriver_path, **kwargs):
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

    chrome_webdriver_kwargs = _get_chrome_webdriver_kwargs(chrome_path, chromedriver_path, **kwargs)

    # contextmanager.__enter__
    try:
        driver = webdriver.Chrome(**chrome_webdriver_kwargs)
    except Exception as e:
        if chrome_path and not os.path.exists(chrome_path):
            raise ChromePdfException(f'Could not find a chrome_path path at: {chrome_path}')
        elif chromedriver_path and not os.path.exists(chromedriver_path):
            raise ChromePdfException(f'Could not find a chromedriver_path at: {chromedriver_path}')
        else:
            raise e

    yield driver

    # contextmanager.__exit__
    driver.quit()  # quits the entire driver (driver.close() only closes the current window)


def _get_chrome_webdriver_kwargs(chrome_path, chromedriver_path, **kwargs):
    """Return the kwargs needed to pass to webdriver.Chrome(), given the CHROMEPDF settings."""

    # at one point "-disable-gpu" was required for headless Chrome. Keep it here just in case.
    # https://bugs.chromium.org/p/chromium/issues/detail?id=737678
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    options.add_argument("--log-level=3")  # silence logging

    # disables the creation of the crash-dumps-dir.
    # will work even if --crash-dumps-dir is provided.
    # keep both as fallbacks. either is preferable to the global default.
    options.add_argument('--disable-crash-reporter')

    # incognito mode lets us run chrome without creating and storing a user profile to disk.
    # this lets us generate PDFs in a thread- and process-safe way since they will not be
    # fighting over reading/writing the same files in the --user-data-dir
    # passing --incognito AND --user-data-dir= WILL cause the user-data-dir folder to be populated, so don't.
    options.add_argument(f"--incognito")

    temp_dir = kwargs.get('_chromesession_temp_dir')
    if temp_dir is not None:
        crash_dumps_dir = os.path.join(temp_dir, 'crash-dumps-dir')
        options.add_argument(f"--crash-dumps-dir={crash_dumps_dir}")

    # add extra chrome args
    chrome_args = kwargs.get('chrome_args', [])
    for argv in chrome_args:
        options.add_argument(argv)

    # silence the "DevTools started" message on windows
    # https://bugs.chromium.org/p/chromedriver/issues/detail?id=2907#c3
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # In Selenium 4, we must tell the driver to ignore any os.environ['http_proxy'/'https_proxy'] values.
    # Calling this function preserves Selenium 3 behavior, which did not check them at all.
    # This function does not exist in Selenium 3, so we must check if it exists to preserve Selenium 3 compatibility.
    # https://github.com/SeleniumHQ/selenium/issues/8768
    if hasattr(options, 'ignore_local_proxy_environment_variables') and callable(options.ignore_local_proxy_environment_variables):
        options.ignore_local_proxy_environment_variables()

    if chrome_path is not None:
        options.binary_location = chrome_path  # Selenium API

    chrome_kwargs = {'options': options}
    if chromedriver_path is not None:
        if _IS_SELENIUM_3:
            chrome_kwargs['executable_path'] = chromedriver_path
        else:
            # executable_path is deprecated in Selenium 4.1.0 - start using Service() instead.
            chrome_kwargs['service'] = Service(chromedriver_path)  # Selenium API

    return chrome_kwargs


def devtool_command(driver, cmd, params={}):
    """
    Send a command to Chrome via the web driver.
    Example:
        result = devtool_command(driver, "Page.printToPDF", pdf_kwargs)
    """

    resource = f"/session/{driver.session_id}/chromium/send_command_and_get_result"
    url = driver.command_executor._url + resource
    body = json.dumps({'cmd': cmd, 'params': params})
    response = driver.command_executor._request('POST', url, body)
    if 'status' in response:
        # response dict only contains a "status" key if an error occurred.
        # when "status" is present, the "value" will contain the error message.
        raise ChromePdfException(response.get('value'))
    return response.get('value')


def _get_chromesession_temp_dir():
    """
    Return an absolute path to a folder to use for storing Chrome's files while making a PDF.

    This is used to store user and crash data locally so that users don't run into permissions issues.
    linux default path for crash dumps as of Chrome 99+ is /tmp/Crashpad/
    which can cause permission errors on startup if different user created it.
    create a separate subfolder for each user to avoid permissions conflicts.
    """

    try:
        username = getpass.getuser()
    except BaseException:
        username = 'default'

    chromesession_dir = os.path.join(os.path.dirname(__file__), 'chromesession')
    user_dir = os.path.join(chromesession_dir, 'users', username)
    return user_dir
