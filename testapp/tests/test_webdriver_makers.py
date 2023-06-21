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
from chromepdf.exceptions import ChromePdfException
from chromepdf.maker import ChromePdfMaker
from chromepdf.pdfconf import clean_pdf_kwargs
from chromepdf.webdrivermakers import get_webdriver_maker_class, is_selenium_installed
from chromepdf.webdrivers import download_chromedriver_version, get_chrome_version
from testapp.tests.utils import createTempFile, extractText, findChromePath


class WebdriverMakerTests(TestCase):

    @override_settings(CHROMEPDF={'CHROME_PATH': '/chrome', 'CHROMEDRIVER_PATH': '/chromedriver', 'CHROME_ARGS': ['--no-sandbox']})
    def test_generate_pdf_maker_args(self):
        """Test to make sure the settings for chromedriver are ultimately passed to it when generating a PDF."""

        html = 'One Word'
        pdfmaker = ChromePdfMaker()
        with patch('chromepdf.maker.get_webdriver_maker') as func:
            with patch('base64.b64decode') as _func2:  # override this so it doesn't complain about not getting a webdriver
                clazz = get_webdriver_maker_class()
                pdfmaker.generate_pdf(html)
                func.assert_called_once_with(clazz, chrome_path='/chrome', chromedriver_path='/chromedriver', _chromesession_temp_dir=pdfmaker._chromesession_temp_dir, chrome_args=['--no-sandbox'])
