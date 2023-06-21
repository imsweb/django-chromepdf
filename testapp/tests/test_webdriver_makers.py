from unittest.case import TestCase
from unittest.mock import patch

from django.test.utils import override_settings

from chromepdf.maker import ChromePdfMaker
from chromepdf.webdrivermakers import get_webdriver_maker_class


class WebdriverMakerTests(TestCase):

    @override_settings(CHROMEPDF={'CHROME_PATH': '/chrome', 'CHROMEDRIVER_PATH': '/chromedriver', 'CHROME_ARGS': ['--no-sandbox']})
    def test_generate_pdf_maker_args(self):
        """Test to make sure the settings for chromedriver are ultimately passed to it when generating a PDF."""

        html = 'Two Words'
        pdfmaker = ChromePdfMaker()
        with patch('chromepdf.maker.get_webdriver_maker') as func:
            with patch('base64.b64decode') as _func2:  # override this so it doesn't complain about not getting a webdriver
                clazz = get_webdriver_maker_class()
                pdfmaker.generate_pdf(html)
                func.assert_called_once_with(clazz, chrome_path='/chrome', chromedriver_path='/chromedriver', _chromesession_temp_dir=pdfmaker._chromesession_temp_dir, chrome_args=['--no-sandbox'])
