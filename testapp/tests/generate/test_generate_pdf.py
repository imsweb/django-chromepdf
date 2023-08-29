import os
import pathlib
import platform
from io import BytesIO
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from unittest.case import TestCase
from unittest.mock import patch

from django.test.utils import override_settings
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from chromepdf import generate_pdf, generate_pdf_url
from chromepdf.conf import parse_settings
from chromepdf.exceptions import ChromePdfException
from chromepdf.maker import ChromePdfMaker
from chromepdf.pdfconf import clean_pdf_kwargs
from chromepdf.webdrivermakers import get_webdriver_maker, get_webdriver_maker_class, is_selenium_installed
from testapp.tests.utils import createTempFile, extractText, findChromePath


# indicate whether selenium will account for missing chromedrivers or not
# See: https://www.selenium.dev/blog/2022/introducing-selenium-manager/
try:
    from selenium.webdriver.common.selenium_manager import SeleniumManager  # pylint: disable=unused-import
    _SELENUIM_WILL_FIX_NONEXISTING_CHROMEDRIVER_PATHS = True

    # the linux chromedriver manager is fixing exists-but-non-executble filepaths but windows is not.
    # linux probably has an easier time checking if is-executable.
    _SELENUIM_WILL_FIX_NONEXECUTABLE_CHROMEDRIVER_PATHS = not (platform.system() == 'Windows')
except Exception:
    _SELENUIM_WILL_FIX_NONEXECUTABLE_CHROMEDRIVER_PATHS = False
    _SELENUIM_WILL_FIX_NONEXISTING_CHROMEDRIVER_PATHS = False


class GeneratePdfSimpleTests(TestCase):
    """
    Test calls to generate_pdf().
    """

    @override_settings(CHROMEPDF={})
    def test_generate_pdf(self):
        """Test outputting a PDF using the generate_pdf() shortcut function."""

        # Actually generate the PDF (slow)
        html = 'Two Words'
        pdfbytes = generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

        # Generating the PDF does go through ChromePdfMaker.generate_pdf() ?
        with patch.object(ChromePdfMaker, '__init__', return_value=None) as init_func:
            with patch.object(ChromePdfMaker, 'generate_pdf', return_value=pdfbytes) as gen_func:

                pdfbytes2 = generate_pdf(html, None)
                self.assertEqual(pdfbytes, pdfbytes2)
                init_func.assert_called_once_with()
                gen_func.assert_called_once_with(html, None)

        # Generating the PDF does go through the webdrivermaker's generate_pdf() ?
        clazz = get_webdriver_maker_class()
        expected_webdriver_kwargs = ChromePdfMaker()._webdriver_kwargs
        with patch.object(clazz, '__init__', return_value=None) as init_func:
            with patch.object(clazz, 'generate_pdf', return_value=pdfbytes) as gen_func:
                with patch.object(clazz, 'quit', return_value=None) as quit_func:

                    pdfbytes2 = generate_pdf(html, None)
                    self.assertEqual(pdfbytes, pdfbytes2)
                    init_func.assert_called_once_with(**expected_webdriver_kwargs)
                    gen_func.assert_called_once_with(html, None)
                    quit_func.assert_called_once_with()

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_kwargs(self):
        """Test outputting a PDF using a ChromePdfMaker object, and passing pdf_kwargs and kwargs."""

        # Actually generate the PDF (slow)
        html = 'Two Words'
        pdf_kwargs = clean_pdf_kwargs()
        kwargs = parse_settings(chrome_args=['--no-sandbox'])  # test with one harmless arg
        pdfbytes = generate_pdf(html, pdf_kwargs, **kwargs)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

        # Generating the PDF does go through ChromePdfMaker.generate_pdf() ?
        with patch.object(ChromePdfMaker, '__init__', return_value=None) as init_func:
            with patch.object(ChromePdfMaker, 'generate_pdf', return_value=pdfbytes) as gen_func:

                pdfbytes2 = generate_pdf(html, pdf_kwargs, **kwargs)
                self.assertEqual(pdfbytes, pdfbytes2)
                init_func.assert_called_once_with(**kwargs)
                gen_func.assert_called_once_with(html, pdf_kwargs)

        # Generating the PDF does go through the webdrivermaker's generate_pdf() ?
        clazz = get_webdriver_maker_class()
        expected_webdriver_kwargs = ChromePdfMaker(**kwargs)._webdriver_kwargs
        with patch.object(clazz, '__init__', return_value=None) as init_func:
            with patch.object(clazz, 'generate_pdf', return_value=pdfbytes) as gen_func:
                with patch.object(clazz, 'quit', return_value=None) as quit_func:

                    pdfbytes2 = generate_pdf(html, pdf_kwargs, **kwargs)
                    self.assertEqual(pdfbytes, pdfbytes2)
                    init_func.assert_called_once_with(**expected_webdriver_kwargs)
                    gen_func.assert_called_once_with(html, pdf_kwargs)
                    quit_func.assert_called_once_with()


class GeneratePdfUrlSimpleTests(TestCase):

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_url(self):
        """Test outputting a PDF using the generate_pdf() shortcut function."""

        # Actually generate the PDF (slow)
        html = 'Two Words'
        file = createTempFile(html)
        file_uri = pathlib.Path(file.name).as_uri()
        pdfbytes = generate_pdf_url(file_uri)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

        # Generating the PDF does go through ChromePdfMaker.generate_pdf() ?
        with patch.object(ChromePdfMaker, '__init__', return_value=None) as init_func:
            with patch.object(ChromePdfMaker, 'generate_pdf_url', return_value=pdfbytes) as gen_func:

                pdfbytes2 = generate_pdf_url(file_uri, None)
                self.assertEqual(pdfbytes, pdfbytes2)
                init_func.assert_called_once_with()
                gen_func.assert_called_once_with(file_uri, None)

        # Generating the PDF does go through the webdrivermaker's generate_pdf() ?
        clazz = get_webdriver_maker_class()
        expected_webdriver_kwargs = ChromePdfMaker()._webdriver_kwargs
        with patch.object(clazz, '__init__', return_value=None) as init_func:
            with patch.object(clazz, 'generate_pdf_url', return_value=pdfbytes) as gen_func:
                with patch.object(clazz, 'quit', return_value=None) as quit_func:

                    pdfbytes2 = generate_pdf_url(file_uri, None)
                    self.assertEqual(pdfbytes, pdfbytes2)
                    init_func.assert_called_once_with(**expected_webdriver_kwargs)
                    gen_func.assert_called_once_with(file_uri, None)
                    quit_func.assert_called_once_with()

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_url_kwargs(self):
        """Test outputting a PDF using a ChromePdfMaker object, and passing pdf_kwargs and kwargs."""

        # Actually generate the PDF (slow)
        html = 'Two Words'
        file = createTempFile(html)
        file_uri = pathlib.Path(file.name).as_uri()
        pdf_kwargs = clean_pdf_kwargs()
        kwargs = parse_settings(chrome_args=['--no-sandbox'])  # test with one harmless arg
        pdfbytes = generate_pdf_url(file_uri, pdf_kwargs, **kwargs)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

        # Generating the PDF does go through ChromePdfMaker.generate_pdf() ?
        with patch.object(ChromePdfMaker, '__init__', return_value=None) as init_func:
            with patch.object(ChromePdfMaker, 'generate_pdf_url', return_value=pdfbytes) as gen_func:

                pdfbytes2 = generate_pdf_url(file_uri, pdf_kwargs, **kwargs)
                self.assertEqual(pdfbytes, pdfbytes2)
                init_func.assert_called_once_with(**kwargs)
                gen_func.assert_called_once_with(file_uri, pdf_kwargs)

        # Generating the PDF does go through the webdrivermaker's generate_pdf() ?
        clazz = get_webdriver_maker_class()
        expected_webdriver_kwargs = ChromePdfMaker(**kwargs)._webdriver_kwargs
        with patch.object(clazz, '__init__', return_value=None) as init_func:
            with patch.object(clazz, 'generate_pdf_url', return_value=pdfbytes) as gen_func:
                with patch.object(clazz, 'quit', return_value=None) as quit_func:

                    pdfbytes2 = generate_pdf_url(file_uri, pdf_kwargs, **kwargs)
                    self.assertEqual(pdfbytes, pdfbytes2)
                    init_func.assert_called_once_with(**expected_webdriver_kwargs)
                    gen_func.assert_called_once_with(file_uri, pdf_kwargs)
                    quit_func.assert_called_once_with()

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_url_bad_file_uri(self):
        """Test outputting a PDF using the generate_pdf_url() shortcut function, with a bad file URI."""

        with self.assertRaises(ValueError):
            _pdfbytes = generate_pdf_url('/bad/absolute/path/not/a/scheme.html')


class GeneratePdfPathTests(TestCase):
    """
    Check to ensure that chrome_path and chromedriver_path args DO impact the ability to generate PDFs
    (are being passed to Selenium correctly).
    For speed, these functions dont actually generate PDFs, just either hit the final method (mocked) or raise exception.
    """

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_chrome_path_success(self):

        # A valid Chrome path should result in the webdriver maker's generate_pdf function being called.
        # EG, there should have been no exceptions raised when starting Chrome
        html = 'Two Words'
        expected_output = b'Two Words'
        chrome_path = findChromePath()
        assert chrome_path is not None
        clazz = get_webdriver_maker_class()
        with patch(f'{clazz.__module__}.{clazz.__qualname__}.generate_pdf', return_value=expected_output) as func:
            pdfbytes = generate_pdf(html, chrome_path=chrome_path)
            self.assertEqual(pdfbytes, expected_output)
            func.assert_called_once_with(html, None)

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_chrome_path_failure(self):
        html = 'Two Words'
        chrome_path = r"C:\Program Files (x86)\badpath.exe"
        with self.assertRaises(ChromePdfException) as exc:
            _pdfbytes = generate_pdf(html, chrome_path=chrome_path)
        expected = f'Tried to determine version of Chrome located at: "{chrome_path}", but no executable exists at that location.'
        self.assertEqual(str(exc.exception), expected)

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_chromedriver_path_failure(self):

        html = 'Two Words'
        expected_output = b'Two Words'
        clazz = get_webdriver_maker_class()
        gen_pdf_path = f'{clazz.__module__}.{clazz.__qualname__}.generate_pdf'

        # a valid file path but not an executable
        if _SELENUIM_WILL_FIX_NONEXECUTABLE_CHROMEDRIVER_PATHS and is_selenium_installed():
            with patch(gen_pdf_path, return_value=expected_output) as func:
                pdfbytes = generate_pdf(html, chromedriver_path=__file__)
                self.assertEqual(pdfbytes, expected_output)
                func.assert_called_once_with(html, None)
        else:
            with self.assertRaises(OSError):
                _pdfbytes = generate_pdf(html, chromedriver_path=__file__)

        # bad file path
        chromedriver_path = r"C:\Program Files (x86)\badpath.exe"
        with self.assertRaises(ChromePdfException):
            _pdfbytes = generate_pdf(html, chromedriver_path=chromedriver_path)


class GeneratePdfThreadTests(TestCase):
    """
    Ensure ChromePF can handle multiple PDFs being generated at the same time.
    With certain command-line arguments (or lack thereof), Chrome will encounter problems
    due to multiple processes fighting over the same temp files.
    This includes the lack of --disable-crash-reporter and --incognito flags, especially on Linux.
    """

    @staticmethod
    def _gen_pdf(num):
        html = 'Two Words'
        _pdfbytes = generate_pdf(html)

    def test_multiprocess(self):
        """Test multiple processes trying to create a PDF at the same time."""

        with Pool() as p:
            results = []
            for i in range(3):
                res = p.apply_async(GeneratePdfThreadTests._gen_pdf, args=(i,))
                results.append(res)
                #print(f'started {i}')

            for i, res in enumerate(results):
                self.assertIsNone(res.get(timeout=10))  # no exception raised?
                #print(f'got {i}')

    def test_multithread(self):
        """Test multiple threads trying to create a PDF at the same time."""

        with ThreadPool() as p:
            results = []
            for i in range(3):
                res = p.apply_async(GeneratePdfThreadTests._gen_pdf, args=(i,))
                results.append(res)
                #print(f'started {i}')

            for i, res in enumerate(results):
                self.assertIsNone(res.get(timeout=10))  # no exception raised?
                #print(f'got {i}')


class GeneratePdfEncodingTests(TestCase):

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_and_url_special_chars(self):
        """
        Test outputting a PDF with special characters.

        One unicode character is tested.
        Also, the Javascript escape character for multi-line strings (due to us using it in document.write(`{}`))
        """

        html = 'Unicode Char: \u0394 Javascript escape character: ` Some quotes: "\''

        # generate_pdf
        pdfbytes = generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

        # generate_pdf_url
        extracted_text = ''
        try:
            tempfile = createTempFile(html)
            tempfile_uri = pathlib.Path(tempfile.name).as_uri()
            pdfbytes = generate_pdf_url(tempfile_uri)
            extracted_text = extractText(pdfbytes).strip()
        finally:
            os.remove(tempfile.name)
        self.assertEqual(1, extracted_text.count(html))


class PdfPageSizeTests(TestCase):
    """
    Test the functions that actually generate the PDFs.

    Uses PikePDF to parse the results.
    """

    def assertPageSizeInInches(self, pdfbytes, expected_size):
        "Assert that the PDF passed has the expected size desired, in inches. E.G., espected_size = (8.5, 11)"

        parser = PDFParser(BytesIO(pdfbytes))
        document = PDFDocument(parser)
        for page in PDFPage.create_pages(document):
            page_rect = page.mediabox
            break

        _, _, w, h = page_rect

        # allow some margin (HA!) of error (2 pixels at 72 dpi)
        self.assertTrue(expected_size[0] * 72 - 2 <= w <= expected_size[0] * 72 + 2)
        self.assertTrue(expected_size[1] * 72 - 2 <= h <= expected_size[1] * 72 + 2)

    @override_settings(CHROMEPDF={})
    def test_sizes(self):

        # use a single chromepdfdriver instance to quickly generate multiple PDFs, instead of starting and stopping
        # Actually generate the PDF (slow)
        html = 'Two Words'
        clazz = get_webdriver_maker_class()
        expected_webdriver_kwargs = ChromePdfMaker()._webdriver_kwargs
        with get_webdriver_maker(clazz, **expected_webdriver_kwargs) as driver:

            # default page size is 8.5 x 11
            pdfbytes = driver.generate_pdf(html, {})
            self.assertPageSizeInInches(pdfbytes, (8.5, 11))

            # default, landscape mode
            pdfbytes = driver.generate_pdf(html, {'landscape': True})
            self.assertPageSizeInInches(pdfbytes, (11, 8.5))

            # Test the effect of a paperFormat override on the generated PDF file's size.
            pdfbytes = driver.generate_pdf(html, {'paperFormat': 'A4'})
            self.assertPageSizeInInches(pdfbytes, (8.26, 11.69))

            # Test the effect of a paperFormat override on the generated PDF file's size when in landscape mode.
            pdfbytes = driver.generate_pdf(html, {'paperFormat': 'A4', 'landscape': True})
            self.assertPageSizeInInches(pdfbytes, (11.69, 8.26))

            # Scale should affect text size, NOT the paper size.
            pdfbytes = driver.generate_pdf(html, {'scale': 2})
            self.assertPageSizeInInches(pdfbytes, (8.5, 11))
