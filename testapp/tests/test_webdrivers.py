import os
import time
from unittest.case import TestCase

from django.test.utils import override_settings

from chromepdf.conf import parse_settings
from chromepdf.exceptions import ChromePdfException
from chromepdf.maker import ChromePdfMaker
from chromepdf.webdrivers import (_get_chrome_webdriver_kwargs,
                                  _get_chromedriver_download_path,
                                  _get_chromedriver_environment_path,
                                  devtool_command,
                                  download_chromedriver_version,
                                  get_chrome_version, get_chrome_webdriver)
from testapp.tests.utils import findChromePath


class ChromeDriverDownloadTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # these tests rely on Selenium to find the chromedriver on PATH. Abort if it's not there.
        if not _get_chromedriver_environment_path():
            raise Exception('You must have `chromedriver/chromedriver.exe` on your PATH for these tests to pass.')

    def test_chromedriver_args(self):

        # ensure default arguments are passed
        with override_settings(CHROMEPDF={}):
            options = _get_chrome_webdriver_kwargs(**parse_settings())['options']
            self.assertEqual(options._arguments, ["--headless", '--disable-gpu', '--log-level=3'])

        # ensure extra added argument from CHROME_ARGS is passed
        with override_settings(CHROMEPDF={'CHROME_ARGS': ['--no-sandbox']}):
            options = _get_chrome_webdriver_kwargs(**parse_settings())['options']
            self.assertEqual(options._arguments, ["--headless", '--disable-gpu', '--log-level=3', "--no-sandbox"])

    @override_settings(CHROMEPDF={})
    def test_chromedriver_downloads(self):
        """
        Test that the chromedriver is downloaded under the right conditions.
        Test the file times of the chromedriver file to see if it's been updated or not.
        """

        chrome_path = findChromePath()
        version = get_chrome_version(chrome_path)

        driver_path = _get_chromedriver_download_path(version[0])

        # delete if it exists, so it will be detected and re-downloaded.
        if os.path.exists(driver_path):
            os.remove(driver_path)

        download_chromedriver_version(version)
        self.assertTrue(os.path.exists(driver_path))
        mtime = os.path.getmtime(driver_path)

        time.sleep(1)  # wait one second

        # should do nothing; already exists
        download_chromedriver_version(version)
        mtime2 = os.path.getmtime(driver_path)
        self.assertEqual(mtime, mtime2)  # time should not have changed.

        time.sleep(1)  # wait one second

        # should force download
        download_chromedriver_version(version, force=True)
        mtime3 = os.path.getmtime(driver_path)
        self.assertNotEqual(mtime, mtime3)  # file was force-updated; time SHOULD have changed.

        time.sleep(1)  # wait one second

        # pdfmaker should auto-download it if chrome path is provided
        if os.path.exists(driver_path):
            os.remove(driver_path)
        _pdfmaker = ChromePdfMaker(chrome_path=chrome_path)
        self.assertTrue(os.path.exists(driver_path))
        mtime = os.path.getmtime(driver_path)

        time.sleep(1)  # wait one second

        # should do nothing; already exists
        _pdfmaker = ChromePdfMaker(chrome_path=chrome_path)
        mtime2 = os.path.getmtime(driver_path)
        self.assertEqual(mtime, mtime2)  # time should not have changed.

    def test_chromedriver_downloads_part2_bad_paths(self):
        """This test MUST come after test_chromedriver_downloads() otherwise os.remove(driver_path) call will fail."""

        bad_path = r'C:\bad_path.exe'
        chrome_path = findChromePath()
        chromedriver_path = download_chromedriver_version(get_chrome_version(chrome_path))

        # bad chrome path should throw exception
        with self.assertRaises(ChromePdfException):
            with get_chrome_webdriver(chrome_path=bad_path, chromedriver_path=chromedriver_path):
                pass

        # bad chromedriver path should throw exception
        with self.assertRaises(ChromePdfException):
            with get_chrome_webdriver(chrome_path=chrome_path, chromedriver_path=bad_path):
                pass

        # don't throw exception
        with get_chrome_webdriver(chrome_path=chrome_path, chromedriver_path=chromedriver_path):
            pass

    def test_devtool_command_failure(self):
        """Make sure bad parameters to devtool_command will raise ChromePdfException."""

        chrome_path = findChromePath()
        chromedriver_path = download_chromedriver_version(get_chrome_version(chrome_path))

        with get_chrome_webdriver(chrome_path=chrome_path, chromedriver_path=chromedriver_path) as driver:
            with self.assertRaises(ChromePdfException):
                # invalid page range should cause a "Page range syntax error" message that we raise as ChromePdfexception
                _result = devtool_command(driver, "Page.printToPDF", {'pageRanges': '3-1'})
