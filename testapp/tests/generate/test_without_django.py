import os
import pathlib
from unittest import mock
from unittest.case import TestCase

from django.test.utils import override_settings

from chromepdf import generate_pdf, generate_pdf_url
from chromepdf.conf import get_chromepdf_settings_dict
from chromepdf.webdrivers import _get_chromedriver_environment_path
from testapp.tests.utils import createTempFile


class TestWithoutDjangoTests(TestCase):
    """
    These tests should be capable of passing with only selenium installed.

    py -3 -m unittest testapp.tests.test_without_django
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # these tests rely on Selenium to find the chromedriver on PATH. Abort if it's not there.
        if not _get_chromedriver_environment_path():
            raise Exception('You must have `chromedriver/chromedriver.exe` on your PATH for these tests to pass.')

    def test_without_django(self):
        """
        Check the chromepdf library to ensure Django is only ever imported once, in get_chromepdf_settings_dict().
        This helps ensure Django never becomes a requirement. Everything should work fine without Django,
        except for pulling in its settings.

        Check that there's only one instance of "django" in the chromepdf files.

        This is a hack-y way of doing it. The other tests here should actually confirm PDFs can generate without Django.
        """

        chromepdf_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'chromepdf'))
        self.assertTrue(os.path.isdir(chromepdf_dir))

        #total_files = 0
        total_count = 0
        for dirpath, _dirs, files in os.walk(chromepdf_dir):
            for name in files:
                if not name.endswith('.py'):
                    continue

                path = os.path.join(dirpath, name)
                with open(path, 'r', encoding='utf8') as f:
                    contents = f.read()
                    total_count += contents.count('django')
                    #total_files += 1

        self.assertEqual(1, total_count)
        #self.assertEqual(8, total_files)

    def test_get_chromepdf_settings_dict(self):

        # Simulate an ImportError by hiding django.conf
        # This should cause import to silently fail. Should return an empty dict even though setting exists.
        with override_settings(CHROMEPDF={'CHROME_PATH': '/path'}):

            # this will simulate ImportError of django.conf
            with mock.patch.dict('sys.modules', {'django.conf': None}):  # @UndefinedVariable

                settings = get_chromepdf_settings_dict()
                self.assertEqual(settings, {})

        # Test when no import error occurs
        with override_settings(CHROMEPDF={'CHROME_PATH': '/path'}):
            settings = get_chromepdf_settings_dict()
            self.assertEqual(settings, {'CHROME_PATH': '/path'})

    def test_generate_pdf_without_django(self):
        """Test outputting a PDF using the generate_pdf() shortcut function."""

        html = 'One Word'
        pdfbytes = generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)

    def test_generate_pdf_url_without_django(self):
        """Test outputting a PDF using the generate_pdf_url() shortcut function."""

        html = "This is a test"
        try:
            tempfile = createTempFile(html)
            tempfile_uri = pathlib.Path(tempfile.name).as_uri()
            pdfbytes = generate_pdf_url(tempfile_uri)
            self.assertIsInstance(pdfbytes, bytes)
        finally:
            os.remove(tempfile.name)
