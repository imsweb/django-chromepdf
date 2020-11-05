import os
import pathlib
import tempfile
from unittest.case import TestCase

from chromepdf.webdrivers import _get_chromedriver_environment_path


def createTempFile(file_bytes):
    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode('utf8')
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(file_bytes)  # 10 bytes
    temp.close()  # close it, so it can be copied from for opens
    return temp


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

        chromepdf_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'chromepdf'))
        self.assertTrue(os.path.isdir(chromepdf_dir))

        #total_files = 0
        total_count = 0
        for dirpath, _dirs, files in os.walk(chromepdf_dir):
            for name in files:
                if not name.endswith('.py'):
                    continue

                path = os.path.join(dirpath, name)
                with open(path, 'r') as f:
                    contents = f.read()
                    total_count += contents.count('django')
                    #total_files += 1

        self.assertEqual(1, total_count)
        #self.assertEqual(8, total_files)

    def test_generate_pdf_without_django(self):
        """Test outputting a PDF using the generate_pdf() shortcut function."""

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = 'One Word'
        pdfbytes = generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)

    def test_generate_pdf_url_without_django(self):
        """Test outputting a PDF using the generate_pdf_url() shortcut function."""

        from chromepdf import generate_pdf_url  # top-level, not via chromepdf.shortcuts

        html = "This is a test"
        try:
            tempfile = createTempFile(html)
            tempfile_uri = pathlib.Path(tempfile.name).as_uri()
            pdfbytes = generate_pdf_url(tempfile_uri)
            self.assertIsInstance(pdfbytes, bytes)
        finally:
            os.remove(tempfile.name)
