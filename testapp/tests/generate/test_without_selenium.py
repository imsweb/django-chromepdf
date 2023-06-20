"""
Runs several other pdf-generation tests, but with the selenium package hidden so that it will
fallback to not using selenium.
"""

from unittest import TestCase, mock

from chromepdf.webdrivermakers import *
from testapp.tests.generate import test_generate_pdf


@mock.patch.dict('sys.modules', {'selenium': None})
class NS_GeneratePdfSimpleTests(test_generate_pdf.GeneratePdfSimpleTests):
    pass


@mock.patch.dict('sys.modules', {'selenium': None})
class NS_GeneratePdfPathTests(test_generate_pdf.GeneratePdfPathTests):
    pass


@mock.patch.dict('sys.modules', {'selenium': None})
class NS_GeneratePdfUrlSimpleTests(test_generate_pdf.GeneratePdfUrlSimpleTests):
    pass


@mock.patch.dict('sys.modules', {'selenium': None})
class NS_GeneratePdfThreadTests(test_generate_pdf.GeneratePdfThreadTests):
    pass


@mock.patch.dict('sys.modules', {'selenium': None})
class NS_GeneratePdfEncodingTests(test_generate_pdf.GeneratePdfEncodingTests):
    pass


@mock.patch.dict('sys.modules', {'selenium': None})
class NS_PdfPageSizeTests(test_generate_pdf.PdfPageSizeTests):
    pass


class SeleniumInstallationTests(TestCase):

    def test_is_selenium_installed(self):
        self.assertTrue(is_selenium_installed())
        with mock.patch.dict('sys.modules', {'selenium': None}):
            self.assertFalse(is_selenium_installed())

    def test_get_webdriver_maker_class(self):

        self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class())
        self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class(None))
        self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class(False))
        self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class(True))

        with mock.patch.dict('sys.modules', {'selenium': None}):
            self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class())
            self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class(None))
            self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class(False))
            self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class(True))
