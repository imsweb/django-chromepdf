"""
Runs several other pdf-generation tests, but with the selenium package hidden so that it will
fallback to not using selenium.
"""

from unittest import TestCase, mock

from chromepdf.maker import ChromePdfMaker
from chromepdf.webdrivermakers import *
from testapp.tests.generate import test_generate_pdf


# This decorator will cause all instances of "import selenium" to fail.
# This makes it easier to test behavior when selenium is not installed.
hide_selenium_install = mock.patch.dict('sys.modules', {'selenium': None})


@hide_selenium_install
class NS_GeneratePdfSimpleTests(test_generate_pdf.GeneratePdfSimpleTests):
    pass


@hide_selenium_install
class NS_GeneratePdfPathTests(test_generate_pdf.GeneratePdfPathTests):
    pass


@hide_selenium_install
class NS_GeneratePdfUrlSimpleTests(test_generate_pdf.GeneratePdfUrlSimpleTests):
    pass


@hide_selenium_install
class NS_GeneratePdfThreadTests(test_generate_pdf.GeneratePdfThreadTests):
    pass


@hide_selenium_install
class NS_GeneratePdfEncodingTests(test_generate_pdf.GeneratePdfEncodingTests):
    pass


@hide_selenium_install
class NS_PdfPageSizeTests(test_generate_pdf.PdfPageSizeTests):
    pass


class SeleniumInstallationTests(TestCase):
    """
    Tests behavior of several functions when selenium is, or isn't, installed.
    """

    def test_is_selenium_installed(self):
        self.assertTrue(is_selenium_installed())
        with hide_selenium_install:
            self.assertFalse(is_selenium_installed())

    def test_get_webdriver_maker_class(self):

        self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class())
        self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class(None))
        self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class(False))
        self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class(True))

        with hide_selenium_install:
            self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class())
            self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class(None))
            self.assertEqual(NoSeleniumWebdriverMaker, get_webdriver_maker_class(False))
            self.assertEqual(SeleniumWebdriverMaker, get_webdriver_maker_class(True))

    def test_maker_class(self):

        self.assertEqual(SeleniumWebdriverMaker, ChromePdfMaker()._clazz)
        self.assertEqual(SeleniumWebdriverMaker, ChromePdfMaker(use_selenium=None)._clazz)
        self.assertEqual(NoSeleniumWebdriverMaker, ChromePdfMaker(use_selenium=False)._clazz)
        self.assertEqual(SeleniumWebdriverMaker, ChromePdfMaker(use_selenium=True)._clazz)

        with hide_selenium_install:
            self.assertEqual(NoSeleniumWebdriverMaker, ChromePdfMaker()._clazz)
            self.assertEqual(NoSeleniumWebdriverMaker, ChromePdfMaker(use_selenium=None)._clazz)
            self.assertEqual(NoSeleniumWebdriverMaker, ChromePdfMaker(use_selenium=False)._clazz)
            self.assertEqual(SeleniumWebdriverMaker, ChromePdfMaker(use_selenium=True)._clazz)
