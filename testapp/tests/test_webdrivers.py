import os
import platform
import time
from unittest import mock
from unittest.case import TestCase

from django.conf import settings
from django.test.utils import override_settings

from chromepdf.conf import parse_settings
from chromepdf.exceptions import ChromePdfException
from chromepdf.maker import ChromePdfMaker
from chromepdf.webdrivers import (
    _get_chrome_webdriver_kwargs, _get_chromedriver_download_path,
    _get_chromedriver_environment_path, _get_chromedriver_zip_url,
    _get_chromesession_temp_dir, devtool_command,
    download_chromedriver_version, get_chrome_version, get_chrome_webdriver)
from testapp.tests.utils import findChromePath


class MockProcessResult:

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout.encode('utf8') if isinstance(stdout, str) else stdout
        self.stderr = stderr.encode('utf8') if isinstance(stderr, str) else stderr


class GetChromeVersionTests(TestCase):

    def test_get_chrome_version(self):
        """Work for current OS. Get it for real. No mocking."""

        path = findChromePath()
        output = get_chrome_version(path)
        self.assertIsInstance(output, tuple)
        self.assertEqual(4, len(output))
        self.assertTrue(isinstance(i, int) for i in output)

    def test_get_chrome_version_windows(self):
        """Mock the Windows method of getting the version."""

        path = findChromePath()
        expected_output = (85, 12, 45, 143)
        output_str = '.'.join(str(i) for i in expected_output)

        with mock.patch('platform.system') as m1:
            m1.return_value = 'Windows'
            with mock.patch('subprocess.run') as m2:
                def side_effect(value, *args, **kwargs):
                    "Powershell should output a table like this when passed a specific command for version info."
                    if value == ['powershell', f'(Get-Item "{path}").VersionInfo']:
                        stdout = f"""
        ProductVersion   FileVersion      FileName
        --------------   -----------      --------
        {output_str}     {output_str}     {path}
        """
                    else:
                        stdout = ''
                    return MockProcessResult(stdout=stdout)
                m2.side_effect = side_effect

                output = get_chrome_version(path)
                self.assertEqual(expected_output, output)

    def test_get_chrome_version_windows_failure(self):
        """Test Windows version when it doesn't output an actual version."""

        path = findChromePath()
        with mock.patch('platform.system') as m1:
            m1.return_value = 'Windows'
            with mock.patch('subprocess.run') as m2:
                m2.return_value = ''

                with self.assertRaises(ChromePdfException):
                    output = get_chrome_version(path)

    def test_get_chrome_version_linux_mac(self):
        """Mock the Linux/Mac method of getting the version."""

        path = findChromePath()
        expected_output = (85, 12, 45, 143)
        output_str = '.'.join(str(i) for i in expected_output)
        output_str = f'Google Chrome {output_str}'  # chrome --version should output a string exactly like this.

        for system in ('Linux', 'Darwin'):
            with mock.patch('platform.system') as m1:
                m1.return_value = system
                with mock.patch('subprocess.run') as m2:
                    def side_effect(value, *args, **kwargs):
                        if value == [path, '--version']:
                            stdout = output_str
                        else:
                            stdout = ''
                        return MockProcessResult(stdout=stdout)
                    m2.side_effect = side_effect

                    output = get_chrome_version(path)
                    self.assertEqual(expected_output, output)

    def test_get_chrome_version_linux_mac_failure(self):
        """Mock the Linux/Mac method of getting the version when it doesn't output an actual version."""

        path = findChromePath()
        for system in ('Linux', 'Darwin'):
            with mock.patch('platform.system') as m1:
                m1.return_value = system
                with mock.patch('subprocess.run') as m2:
                    m2.return_value = ''

                    with self.assertRaises(ChromePdfException):
                        output = get_chrome_version(path)


class GetChromedriverDownloadPathTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # these tests rely on Selenium to find the chromedriver on PATH. Abort if it's not there.
        if not _get_chromedriver_environment_path():
            raise Exception('You must have `chromedriver/chromedriver.exe` on your PATH for these tests to pass.')

    def test_current_os(self):
        """Just call the function. Results will differ depending on OS."""

        major_version = 25
        path = _get_chromedriver_download_path(major_version)

        is_windows = (platform.system() == 'Windows')
        if is_windows:
            expected_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{major_version}.exe')
        else:
            expected_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{major_version}')
        self.assertTrue(expected_path, path)

    def test_mocked_oses(self):
        """Mock several OSes and make sure they return the right paths."""

        major_version = 25
        win_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{major_version}.exe')
        lin_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{major_version}')
        OS_TESTS = {
            'Windows': win_path,
            'Linux': lin_path,
            'Darwin': lin_path,
        }
        for system, expected_path in OS_TESTS.items():
            with self.subTest(system=system):
                with mock.patch('platform.system') as m1:
                    m1.return_value = system
                    self.assertEqual(expected_path, _get_chromedriver_download_path(major_version))


class GetChromedriverZipUrlTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # these tests rely on Selenium to find the chromedriver on PATH. Abort if it's not there.
        if not _get_chromedriver_environment_path():
            raise Exception('You must have `chromedriver/chromedriver.exe` on your PATH for these tests to pass.')

    def test_current_os(self):
        """Just call the function. Results will differ depending on OS."""

        chromedriver_version = '85.5.6.114'
        url = _get_chromedriver_zip_url(chromedriver_version)

        self.assertTrue(url.startswith(f'https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_'))
        self.assertTrue(url.endswith('.zip'))

    def test_mocked_oses(self):
        """Mock several OSes and make sure they return the right paths."""

        chromedriver_version = '85.5.6.114'
        OS_TESTS = {
            ('Windows', 'amdk6'): 'win32',
            ('Linux', 'amdk6'): 'linux64',
            ('Darwin', 'amdk6'): 'mac64',
            ('Darwin', 'arm'): 'mac64_m1',
        }
        for system_processor, expected_zip in OS_TESTS.items():
            expected_path = f'https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_{expected_zip}.zip'
            system, processor = system_processor
            with self.subTest(system=system, processor=processor):
                with mock.patch('platform.system') as m1:
                    m1.return_value = system
                    with mock.patch('platform.processor') as m2:
                        m2.return_value = processor
                        self.assertEqual(expected_path, _get_chromedriver_zip_url(chromedriver_version))


class ChromeDriverDownloadTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # these tests rely on Selenium to find the chromedriver on PATH. Abort if it's not there.
        if not _get_chromedriver_environment_path():
            raise Exception('You must have `chromedriver/chromedriver.exe` on your PATH for these tests to pass.')

    def test_chromedriver_args(self):

        tempdir = _get_chromesession_temp_dir()
        crash_dumps_dir = os.path.join(tempdir, 'crash-dumps-dir')
        userpatharg1 = f'--crash-dumps-dir={crash_dumps_dir}'

        # ensure default arguments are passed
        with override_settings(CHROMEPDF={}):
            options = _get_chrome_webdriver_kwargs(**parse_settings())['options']
            self.assertEqual(options._arguments, ["--headless", '--disable-gpu', '--log-level=3', '--disable-crash-reporter', '--incognito'])

        # ensure default arguments are passed
        with override_settings(CHROMEPDF={}):
            options = _get_chrome_webdriver_kwargs(_chromesession_temp_dir=tempdir, **parse_settings())['options']
            self.assertEqual(options._arguments, ["--headless", '--disable-gpu', '--log-level=3', '--disable-crash-reporter', '--incognito', userpatharg1])

        # ensure extra added argument from CHROME_ARGS is passed
        with override_settings(CHROMEPDF={'CHROME_ARGS': ['--no-sandbox']}):
            options = _get_chrome_webdriver_kwargs(_chromesession_temp_dir=tempdir, **parse_settings())['options']
            self.assertEqual(options._arguments, ["--headless", '--disable-gpu', '--log-level=3', '--disable-crash-reporter', '--incognito', userpatharg1, "--no-sandbox"])

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
        pdfmaker = ChromePdfMaker(chrome_path=chrome_path)
        self.assertTrue(os.path.exists(driver_path))
        # Downloading a chromedriver should cause the maker's internal "settings" to be updated.
        self.assertEqual(pdfmaker._chromedriver_path, driver_path)
        self.assertEqual(pdfmaker._webdriver_kwargs['chromedriver_path'], driver_path)
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

    def test_chromedriver_downloads_part3_kwargs_unchanged(self):
        """
        get_chrome_webdriver() should not change the arguments passed into it.
        This test ensures that successive calls using the same settings dict won't change it.
        This especially applies to the _webdriver_kwargs dict in the ChromePdfMaker class.
        """

        chrome_path = findChromePath()
        chromedriver_path = download_chromedriver_version(get_chrome_version(chrome_path))

        kwargs = {
            'chrome_path': chrome_path,
            'chromedriver_path': chromedriver_path,
            'chrome_args': ['--no-sandbox']
        }

        # should especially not change kwargs
        _get_chrome_webdriver_kwargs(**kwargs)

        # should not change kwargs
        with get_chrome_webdriver(**kwargs):
            pass

        # kwargs was unchanged by pop etc commands?
        self.assertEqual(3, len(kwargs))

    def test_devtool_command_failure(self):
        """Make sure bad parameters to devtool_command will raise ChromePdfException."""

        chrome_path = findChromePath()
        chromedriver_path = download_chromedriver_version(get_chrome_version(chrome_path))

        with get_chrome_webdriver(chrome_path=chrome_path, chromedriver_path=chromedriver_path) as driver:
            with self.assertRaises(ChromePdfException):
                # invalid page range should cause a "Page range syntax error" message that we raise as ChromePdfexception
                _result = devtool_command(driver, "Page.printToPDF", {'pageRanges': '3-1'})
