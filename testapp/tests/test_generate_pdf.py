import json
import os
import pathlib
import tempfile
from io import BytesIO
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from unittest.case import TestCase
from unittest.mock import patch

from django.conf import settings  # @UnusedImport
from django.test.utils import override_settings
from pikepdf import Pdf

from chromepdf.exceptions import ChromePdfException
from chromepdf.maker import ChromePdfMaker
from chromepdf.pdfconf import clean_pdf_kwargs
from chromepdf.webdrivers import (download_chromedriver_version,
                                  get_chrome_version)
from testapp.tests.test_without_django import createTempFile
from testapp.tests.utils import extractText, findChromePath


class GeneratePdfSimpleTests(TestCase):

    @override_settings(CHROMEPDF={})
    def test_generate_pdf(self):
        """Test outputting a PDF using the generate_pdf() shortcut function."""

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = 'One Word'
        pdfbytes = generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_maker(self):
        """Test outputting a PDF using a ChromePdfMaker object, without passing a pdf_kwargs."""

        html = 'One Word'
        pdfmaker = ChromePdfMaker()
        pdfbytes = pdfmaker.generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_maker_with_pdf_kwargs(self):
        """Test outputting a PDF using a ChromePdfMaker object, and passing pdf_kwargs."""

        html = 'One Word'
        pdfmaker = ChromePdfMaker()
        pdfbytes = pdfmaker.generate_pdf(html, clean_pdf_kwargs())
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

    @override_settings(CHROMEPDF={'CHROME_PATH': '/chrome', 'CHROMEDRIVER_PATH': '/chromedriver', 'CHROME_ARGS': ['--no-sandbox']})
    def test_generate_pdf_maker_args(self):
        """Test to make sure the settings for chromedriver are ultimately passed to it when generating a PDF."""

        html = 'One Word'
        pdfmaker = ChromePdfMaker()
        with patch('chromepdf.maker.get_chrome_webdriver') as func:
            with patch('base64.b64decode') as _func2:  # override this so it doesn't complain about not getting a webdriver

                pdfmaker.generate_pdf(html)
                func.assert_called_once_with(chrome_path='/chrome', chromedriver_path='/chromedriver', _chromesession_temp_dir=pdfmaker._chromesession_temp_dir, chrome_args=['--no-sandbox'])


class GeneratePdfPathTests(TestCase):
    """Check to ensure that chrome_path and chromedriver_path args DO impact the ability to generate PDFs (are being passed to Selenium correctly)."""

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_chrome_path_success(self):

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = 'One Word'
        pdfbytes = generate_pdf(html, chrome_path=findChromePath())
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_chrome_path_failure(self):

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = 'One Word'
        with self.assertRaises(ChromePdfException):
            _pdfbytes = generate_pdf(html, chrome_path=r"C:\Program Files (x86)\badpath.exe")

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_chromedriver_path_success(self):

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        chromedriver_path = download_chromedriver_version(get_chrome_version(findChromePath()))

        # no-sandbox needed to work on CI.
        html = 'One Word'
        pdfbytes = generate_pdf(html, chromedriver_path=chromedriver_path, chrome_args=['--no-sandbox'])
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_chromedriver_path_failure(self):

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = 'One Word'
        with self.assertRaises(ChromePdfException):
            _pdfbytes = generate_pdf(html, chromedriver_path=r"C:\Program Files (x86)\badpath.exe")


class GeneratePdfUrlSimpleTests(TestCase):

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_url(self):
        """Test outputting a PDF using the generate_pdf_url() shortcut function."""

        from chromepdf import generate_pdf_url  # top-level, not via chromepdf.shortcuts

        html = "This is a test"
        extracted_text = ''
        try:
            tempfile = createTempFile(html)
            tempfile_uri = pathlib.Path(tempfile.name).as_uri()
            pdfbytes = generate_pdf_url(tempfile_uri)
            self.assertIsInstance(pdfbytes, bytes)
            extracted_text = extractText(pdfbytes)
        finally:
            os.remove(tempfile.name)

        self.assertEqual(1, extracted_text.count(html))

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_url_bad_file_uri(self):
        """Test outputting a PDF using the generate_pdf_url() shortcut function, with a bad file URI."""

        from chromepdf import generate_pdf_url  # top-level, not via chromepdf.shortcuts

        with self.assertRaises(ValueError):
            _pdfbytes = generate_pdf_url('/bad/absolute/path/not/a/scheme.html')

    @override_settings(CHROMEPDF={'CHROME_PATH': '/chrome', 'CHROMEDRIVER_PATH': '/chromedriver', 'CHROME_ARGS': ['--no-sandbox']})
    def test_generate_pdf_url_maker_args(self):
        """Test to make sure the settings for chromedriver are ultimately passed to it when generating a PDF."""

        pdfmaker = ChromePdfMaker()
        with patch('chromepdf.maker.get_chrome_webdriver') as func:
            with patch('base64.b64decode') as _func2:  # override this so it doesn't complain about not getting a webdriver

                pdfmaker.generate_pdf_url('file:///some/file')
                func.assert_called_once_with(chrome_path='/chrome', chromedriver_path='/chromedriver', _chromesession_temp_dir=pdfmaker._chromesession_temp_dir, chrome_args=['--no-sandbox'])


class GeneratePdfThreadTests(TestCase):

    @staticmethod
    def _gen_pdf(num):
        html = 'One Word'
        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts
        _pdfbytes = generate_pdf(html)

    def test_multiprocess(self):
        """Test two processes trying to create a PDF at the same time."""

        p = Pool()
        results = []
        for i in range(3):
            res = p.apply_async(GeneratePdfThreadTests._gen_pdf, args=(i,))
            results.append(res)
            #print(f'started {i}')

        for i, res in enumerate(results):
            self.assertIsNone(res.get(timeout=10))  # no exception raised?
            #print(f'got {i}')

    def test_multithread(self):
        """Test two threads trying to create a PDF at the same time."""

        p = ThreadPool()
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

        from chromepdf import generate_pdf, generate_pdf_url  # top-level, not via chromepdf.shortcuts

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
        pdf = Pdf.open(BytesIO(pdfbytes))

        # this gives us a 4-length list similar to: [0, 0, 612, 792] for an 8.5x11 page.
        page_rect = pdf.pages[0].MediaBox
        page_rect = json.loads(page_rect.to_json().decode('utf8'))  # there must be an easier way...
        _, _, w, h = page_rect

        # allow some margin of error (2 pixels at 72 dpi)
        self.assertTrue(expected_size[0] * 72 - 2 <= w <= expected_size[0] * 72 + 2)
        self.assertTrue(expected_size[1] * 72 - 2 <= h <= expected_size[1] * 72 + 2)

    @override_settings(CHROMEPDF={})
    def test_default_size(self):
        ""

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts
        html = ''
        pdfbytes = generate_pdf(html)

        # default page size is 8.5 x 11
        self.assertPageSizeInInches(pdfbytes, (8.5, 11))

    @override_settings(CHROMEPDF={})
    def test_default_size_landscape(self):
        ""

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = ''
        pdfbytes = generate_pdf(html, {'landscape': True})

        # default page size is 8.5 x 11
        self.assertPageSizeInInches(pdfbytes, (11, 8.5))

    @override_settings(CHROMEPDF={})
    def test_papersize_override(self):
        ""

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = ''
        pdfbytes = generate_pdf(html, {'paperFormat': 'A4'})
        self.assertPageSizeInInches(pdfbytes, (8.26, 11.69))

    @override_settings(CHROMEPDF={})
    def test_papersize_override_landscape(self):
        ""

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = ''
        pdfbytes = generate_pdf(html, {'paperFormat': 'A4', 'landscape': True})
        self.assertPageSizeInInches(pdfbytes, (11.69, 8.26))

    @override_settings(CHROMEPDF={})
    def test_scale(self):
        "Scale should affect text size, NOT the paper size."

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = ''
        pdfbytes = generate_pdf(html, {'scale': 2})
        self.assertPageSizeInInches(pdfbytes, (8.5, 11))
