import copy
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
    _force_version_str, _get_chrome_webdriver_kwargs, _get_chromedriver_download_path,
    _get_chromedriver_environment_path, _get_chromedriver_zip_url, _get_chromesession_temp_dir, _version_to_tuple,
    devtool_command, download_chromedriver_version, get_chrome_version, get_chrome_webdriver)
from testapp.tests.utils import MockCompletedProcess, findChromePath


# indicate whether selenium will account for missing chromedrivers or not
# See: https://www.selenium.dev/blog/2022/introducing-selenium-manager/
try:
    from selenium.webdriver.common.selenium_manager import SeleniumManager  # pylint: disable=unused-import
    _SELENIUM_WILL_FIX_MISSING_CHROMEDRIVERS = True
except Exception:
    _SELENIUM_WILL_FIX_MISSING_CHROMEDRIVERS = False


class LocalChromedriverTestCase(TestCase):
    """TestCase for tests that need a local chromedriver to exist in the current working directory."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # these tests rely on Selenium to find the chromedriver on PATH. Abort if it's not there.
        if not _get_chromedriver_environment_path():
            raise Exception('You must have `chromedriver/chromedriver.exe` on your PATH for these tests to pass.')


class GetChromeVersionTests(TestCase):

    def test_version_conversion(self):
        """Test functions that convert versions between types."""

        version_str = '85.12.45.143'
        version_tpl = (85, 12, 45, 143)
        self.assertEqual(version_tpl, _version_to_tuple(version_str))
        self.assertEqual(version_str, _force_version_str(version_tpl))
        self.assertEqual(version_str, _force_version_str(_version_to_tuple(version_str)))

    def test_get_chrome_version(self):
        """Work for current OS. Get it for real. No mocking."""

        # TODO: in ChromePDF 2.0, get_chrome_version() will always return a string.
        # And as_tuple will raise a warning if it's passed, regardless of value.
        path = findChromePath()
        output = get_chrome_version(path)
        self.assertIsInstance(output, tuple)
        self.assertEqual(4, len(output))
        self.assertTrue(isinstance(i, int) for i in output)

        output2 = get_chrome_version(path, as_tuple=True)
        self.assertEqual(output, output2)

        output3 = get_chrome_version(path, as_tuple=False)
        self.assertEqual('.'.join(str(i) for i in output), output3)

    def test_get_chrome_version_windows(self):
        """Mock the Windows method of getting the version."""

        path = findChromePath()
        expected_version = '85.12.45.143'

        with mock.patch('platform.system') as m1:
            m1.return_value = 'Windows'
            with mock.patch('subprocess.run') as m2:
                def side_effect(value, *args, **kwargs):
                    "Powershell should output a table like this when passed a specific command for version info."
                    if value == ['powershell', f'(Get-Item "{path}").VersionInfo']:
                        stdout = f"""
        ProductVersion   FileVersion      FileName
        --------------   -----------      --------
        {expected_version}     {expected_version}     {path}
        """
                    else:
                        stdout = ''
                    return MockCompletedProcess(stdout=stdout)
                m2.side_effect = side_effect

                output = get_chrome_version(path, as_tuple=False)
                self.assertEqual(expected_version, output)

    def test_get_chrome_version_windows_failure(self):
        """Test Windows version when it doesn't output an actual version."""

        path = findChromePath()
        with mock.patch('platform.system') as m1:
            m1.return_value = 'Windows'
            with mock.patch('subprocess.run') as m2:
                m2.return_value = MockCompletedProcess('')

                with self.assertRaises(ChromePdfException):
                    output = get_chrome_version(path, as_tuple=False)

    def test_get_chrome_version_linux_mac(self):
        """Mock the Linux/Mac method of getting the version."""

        path = findChromePath()
        expected_version = '85.12.45.143'
        output_str = f'Google Chrome {expected_version}'  # chrome --version should output a string exactly like this.

        for system in ('Linux', 'Darwin'):
            with mock.patch('platform.system') as m1:
                m1.return_value = system
                with mock.patch('subprocess.run') as m2:
                    def side_effect(value, *args, **kwargs):
                        if value == [path, '--version']:
                            stdout = output_str
                        else:
                            stdout = ''
                        return MockCompletedProcess(stdout=stdout)
                    m2.side_effect = side_effect

                    output = get_chrome_version(path, as_tuple=False)
                    self.assertEqual(expected_version, output)

    def test_get_chrome_version_linux_mac_failure(self):
        """Mock the Linux/Mac method of getting the version when it doesn't output an actual version."""

        path = findChromePath()
        for system in ('Linux', 'Darwin'):
            with mock.patch('platform.system') as m1:
                m1.return_value = system
                with mock.patch('subprocess.run') as m2:
                    m2.return_value = MockCompletedProcess('')

                    with self.assertRaises(ChromePdfException):
                        output = get_chrome_version(path, as_tuple=False)


class GetChromedriverDownloadPathTests(LocalChromedriverTestCase):

    def test_current_os(self):
        """Just call the function. Results will differ depending on OS."""

        version = '85.12.45.143'
        path = _get_chromedriver_download_path(version)

        is_windows = (platform.system() == 'Windows')
        if is_windows:
            expected_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{version}.exe')
        else:
            expected_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{version}')
        self.assertTrue(expected_path, path)

    def test_mocked_oses(self):
        """Mock several OSes and make sure they return the right paths."""

        version = '85.12.45.143'
        win_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{version}.exe')
        lin_path = os.path.join(settings.BASE_DIR, 'chromepdf', 'chromedrivers', f'chromedriver_{version}')
        OS_TESTS = {
            'Windows': win_path,
            'Linux': lin_path,
            'Darwin': lin_path,
        }
        for system, expected_path in OS_TESTS.items():
            with self.subTest(system=system):
                with mock.patch('platform.system') as m1:
                    m1.return_value = system
                    self.assertEqual(expected_path, _get_chromedriver_download_path(version))


class GetChromedriverZipUrlTests(LocalChromedriverTestCase):

    def test_current_os(self):
        """Just call the function. Results will differ depending on OS."""

        chromedriver_version = '85.5.6.114'
        url = _get_chromedriver_zip_url(chromedriver_version)

        prefix = f'https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_'
        valid_os_types = ('win32', 'linux64', 'mac64', 'mac64_m1')
        suffix = '.zip'
        self.assertTrue(url.startswith(prefix))
        self.assertTrue(url[len(prefix):-len(suffix)] in valid_os_types)
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


class ChromeDriverDownloadTests(LocalChromedriverTestCase):

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
        version = get_chrome_version(chrome_path, as_tuple=False)
        driver_path = _get_chromedriver_download_path(version)

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
        chromedriver_path = download_chromedriver_version(get_chrome_version(chrome_path, as_tuple=False))

        # bad chrome path should throw exception
        with self.assertRaises(ChromePdfException):
            with get_chrome_webdriver(chrome_path=bad_path, chromedriver_path=chromedriver_path):
                pass

        # bad chromedriver path should throw exception...
        # But in Selenium 4.6.0, they added the SeleniumManager (in beta) which will try to automatically download
        # it in the event that the provided chromedriver path does not exist.
        # See: https://www.selenium.dev/blog/2022/introducing-selenium-manager/
        if _SELENIUM_WILL_FIX_MISSING_CHROMEDRIVERS:
            # no exception for missing chromedriver path. selenium will fix it.
            with get_chrome_webdriver(chrome_path=chrome_path, chromedriver_path=bad_path):
                pass
        else:
            # assert an exception. selenium won't fix it.
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
        chromedriver_path = download_chromedriver_version(get_chrome_version(chrome_path, as_tuple=False))

        kwargs = {
            'chrome_path': chrome_path,
            'chromedriver_path': chromedriver_path,
            'chrome_args': ['--no-sandbox']
        }
        kwargs_original = copy.deepcopy(kwargs)

        # should especially not change kwargs
        _get_chrome_webdriver_kwargs(**kwargs)

        # should not change kwargs
        with get_chrome_webdriver(**kwargs):
            pass

        # kwargs was unchanged by pop etc commands?
        self.assertEqual(kwargs_original, kwargs)

    def test_devtool_command_failure(self):
        """Make sure bad parameters to devtool_command will raise ChromePdfException."""

        chrome_path = findChromePath()
        chromedriver_path = download_chromedriver_version(get_chrome_version(chrome_path, as_tuple=False))

        with get_chrome_webdriver(chrome_path=chrome_path, chromedriver_path=chromedriver_path) as driver:
            with self.assertRaises(ChromePdfException):
                # invalid page range should cause a "Page range syntax error" message that we raise as ChromePdfexception
                _result = devtool_command(driver, "Page.printToPDF", {'pageRanges': '3-1'})
