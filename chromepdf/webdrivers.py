import getpass
import io
import json
import os
import platform
import shutil
import subprocess
import warnings
import zipfile
from contextlib import contextmanager
from subprocess import PIPE
from urllib import request as urllib_request

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from chromepdf.exceptions import ChromePdfException


_IS_SELENIUM_3 = selenium.__version__.split('.')[0] == '3'


def _version_to_tuple(version):
    """
    Shortcut function that converts version string to tuple, for allowing deprecated behavior.
    In ChromePDF 2.0, this should no longer be needed. Tuple support will no longer exist.
    """
    return tuple(int(i) for i in version.split('.'))


def _force_version_str(version):
    """
    Shortcut function that lets us accept tuple versions and force them into string versions.
    In ChromePDF 2.0, this should no longer be needed. Tuple support will no longer exist.
    """
    if isinstance(version, tuple):
        warnings.warn("Support for versions as tuples is now deprecated. Pass a string instead.", DeprecationWarning)
        return '.'.join(str(i) for i in version)
    return version


def _get_chrome_version_str(path):
    """
    Return a string containing the version number of the Chrome binary exe, EG for Chrome 85: '85.0.4183.121'
    raise ChromePdfException otherwise (EG if path not found)
    """

    is_windows = (platform.system() == 'Windows')

    try:
        if is_windows:
            cmd = f'(Get-Item "{path}").VersionInfo'
            proc = subprocess.run(['powershell', cmd], check=True, stdout=PIPE, stderr=PIPE)
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
                    return l.split()[0]

            # if no lines containing version numbers were output
            raise ChromePdfException(f'Could not determine version of Chrome executable located at: "{path}"')

        else:  # linux, mac can both just use "--version"
            proc = subprocess.run([path, '--version'], check=True, stdout=PIPE, stderr=PIPE)
            version_stdout = proc.stdout.decode('utf8').strip()  # returns, eg, "Google Chrome 85.0.4183.121"
            return [i for i in version_stdout.split() if i[0].isdigit()][0]

    except Exception as ex:
        # FileNotFoundError, CalledProcessError, IndexError, etc
        if os.path.exists(path):
            exception_msg = f'Could not determine version of Chrome located at: "{path}"'
        else:
            exception_msg = f'Tried to determine version of Chrome located at: "{path}", but no executable exists at that location.'
        raise ChromePdfException(exception_msg) from ex


def get_chrome_version(path, as_tuple=True):
    """
    Return a 4-tuple containing the version number of the Chrome binary exe, EG for Chrome 85: (85,0,4183,121)
    Return a string instead if as_tuple=True is passed.
    raise ChromePdfException otherwise (EG if path not found)
    """

    version = _get_chrome_version_str(path)
    if as_tuple:
        warnings.warn("get_chrome_version() support for returning tuples is deprecated. Pass as_tuple=False instead. In ChromePDF 2.0, this function will return string values always.", DeprecationWarning)
        return _version_to_tuple(version)
    return version


def _get_chromedriver_environment_path():
    """
    Return full path of chromedriver on PATH, if it exists. Otherwise, return None.
    This can be used to determine if Selenium can find the chromedriver without having to specify its location.
    """

    is_windows = (platform.system() == 'Windows')
    filename = 'chromedriver.exe' if is_windows else 'chromedriver'
    return shutil.which(filename)


def _get_chromedriver_download_path(version):
    """Return a path to put/find a chromedriver file, if ChromePDF should/did download it."""

    version = _force_version_str(version)
    is_windows = (platform.system() == 'Windows')
    chromedrivers_dir = os.path.join(os.path.dirname(__file__), 'chromedrivers')
    chromedriver_path = os.path.join(chromedrivers_dir, f'chromedriver_{version}')
    if is_windows:  # windows requires an extension or it won't run.
        chromedriver_path += '.exe'
    else:  # linux, mac = no extension
        pass
    return chromedriver_path


def _fetch_chromedriver_version_for_chrome_version(version):
    """
    Fetch the chromedriver version needed for the given Chrome version by querying the official website.
    Returns a version string such as "85.0.4183.87"
    """

    version = _force_version_str(version)

    # Google's API for the latest release takes only the first 3 parts of the version
    version_first3parts = version.rsplit('.', maxsplit=1)[0]  # EG, "85.0.4183"

    # This url returns a 4-part version string of the latest compatible chromedriver for your Chrome version.
    # This might be DIFFERENT than the version of your Chrome executable.
    url = f'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version_first3parts}'
    with urllib_request.urlopen(url) as f:
        contents = f.read()
    chromedriver_version = contents.decode('utf8')  # EG "85.0.4183.87"
    return chromedriver_version


def _get_chromedriver_zip_url(chromedriver_version):
    """
    Get the chromedriver zip download url for our particular OS+Processor.
    The possible urls are taken from the chromedriver release files list, here:
    https://chromedriver.chromium.org/downloads
    """

    is_windows = (platform.system() == 'Windows')
    is_mac = (platform.system() == 'Darwin')
    is_mac_m1 = (is_mac and platform.processor() == 'arm')

    if is_windows:
        os_plus_numbits = 'win32'
    elif is_mac_m1:
        os_plus_numbits = 'mac64_m1'
    elif is_mac:
        os_plus_numbits = 'mac64'
    else:
        os_plus_numbits = 'linux64'
    filename = f'chromedriver_{os_plus_numbits}.zip'

    return f'https://chromedriver.storage.googleapis.com/{chromedriver_version}/{filename}'


def _fetch_chromedriver_zip_bytes(chromedriver_version):
    """
    Return the bytes of the chromedriver zip file for the given chromedriver version, for our OS.
    """

    url = _get_chromedriver_zip_url(chromedriver_version)
    with urllib_request.urlopen(url) as f:
        zip_bytes = f.read()
    return zip_bytes


def download_chromedriver_version(version, force=False):
    """
    Download a chromedriver executable for the Chrome version specified, if not already downloaded or force=True.
    Return the path of the existing (or newly downloaded) chromedriver executable.

    See https://chromedriver.chromium.org/downloads/version-selection
    for download url api

    Arguments:
    * version: A version string as returned by get_chrome_version(), such as: '85.0.4183.121'
    * force: If True, will force a download, even if a driver for that version is already saved.
    """

    version = _force_version_str(version)

    # Return the existing path if it exists and we're not forcing a new download.
    chromedriver_download_path = _get_chromedriver_download_path(version)
    if os.path.exists(chromedriver_download_path) and not force:
        return chromedriver_download_path

    # chromedrivers have their own version strings. fetch the one for our chrome version.
    chromedriver_version = _fetch_chromedriver_version_for_chrome_version(version)

    # Download the zip file containing our chromedriver
    zip_bytes = _fetch_chromedriver_zip_bytes(chromedriver_version)

    # Open the zip file, find the chromedriver, and save it to the specified path.
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
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


def _get_chrome_webdriver_args(**kwargs):

    args = []

    args.append("--headless")
    args.append("--disable-gpu")

    args.append("--log-level=3")  # silence logging

    # disables the creation of the crash-dumps-dir.
    # will work even if --crash-dumps-dir is provided.
    # keep both as fallbacks. either is preferable to the global default.
    args.append('--disable-crash-reporter')

    # incognito mode lets us run chrome without creating and storing a user profile to disk.
    # this lets us generate PDFs in a thread- and process-safe way since they will not be
    # fighting over reading/writing the same files in the --user-data-dir
    # passing --incognito AND --user-data-dir= WILL cause the user-data-dir folder to be populated, so don't.
    args.append("--incognito")

    temp_dir = kwargs.get('_chromesession_temp_dir')
    if temp_dir is not None:
        crash_dumps_dir = os.path.join(temp_dir, 'crash-dumps-dir')
        args.append(f"--crash-dumps-dir={crash_dumps_dir}")

    # add extra chrome args
    chrome_args = kwargs.get('chrome_args', [])
    for argv in chrome_args:
        args.append(argv)

    return args


def _get_chrome_webdriver_kwargs(chrome_path, chromedriver_path, **kwargs):
    """Return the kwargs needed to pass to webdriver.Chrome(), given the CHROMEPDF settings."""

    options = webdriver.ChromeOptions()

    args = _get_chrome_webdriver_args(**kwargs)
    for arg in args:
        options.add_argument(arg)

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


def devtool_command(driver, cmd, params=None):
    """
    Send a command to Chrome via the web driver.
    Example:
        result = devtool_command(driver, "Page.printToPDF", pdf_kwargs)
    """

    if params is None:
        params = {}
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
    except Exception:
        username = 'default'

    chromesession_dir = os.path.join(os.path.dirname(__file__), 'chromesession')
    user_dir = os.path.join(chromesession_dir, 'users', username)
    return user_dir
