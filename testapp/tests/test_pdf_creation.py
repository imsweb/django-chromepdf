import os
import pathlib
import tempfile
from io import BytesIO
from unittest.case import TestCase

from django.conf import settings  # @UnusedImport
from django.test.utils import override_settings
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from PyPDF2 import PdfFileReader

from chromepdf.maker import ChromePdfMaker
from chromepdf.pdfconf import clean_pdf_kwargs


def extractText(pdfbytes):
    """Use pdfminer to take a pdf file-like-object/stream and return its text."""
    import io

    fp = BytesIO(pdfbytes)

    retstr = io.BytesIO()
    laparams = LAParams()

    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, retstr, codec='utf-8', laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(fp, caching=True, check_extractable=True):
        interpreter.process_page(page)
    text = retstr.getvalue()
    device.close()
    retstr.close()
    if not isinstance(text, str):
        text = text.decode('utf8')
    return text


def createTempFile(file_bytes):
    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode('utf8')
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(file_bytes)  # 10 bytes
    temp.close()  # close it, so it can be copied from for opens
    return temp


class GeneratePdfTests(TestCase):

    @override_settings(CHROMEPDF={})
    def test_generate_pdf(self):
        """Test outputting a PDF using the generate_pdf() shortcut function."""

        from chromepdf import generate_pdf  # top-level, not via chromepdf.shortcuts

        html = 'One Word'
        pdfbytes = generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

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
    def test_generate_pdf_maker(self):
        """Test outputting a PDF using a ChromePdfMaker object."""

        html = 'One Word'
        pdfmaker = ChromePdfMaker()
        pdfbytes = pdfmaker.generate_pdf(html, clean_pdf_kwargs())
        self.assertIsInstance(pdfbytes, bytes)
        self.assertEqual(1, extractText(pdfbytes).count(html))

    @override_settings(CHROMEPDF={})
    def test_generate_pdf_special_chars(self):
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

    Uses PyPDF2 to parse the results.
    """

    def assertPageSizeInInches(self, pdfbytes, expected_size):
        reader = PdfFileReader(BytesIO(pdfbytes))
        page_rect = reader.getPage(0).mediaBox

        # allow some margin of error (2 pixels at 72 dpi)
        self.assertTrue(expected_size[0] * 72 - 2 <= page_rect.upperRight[0] <= expected_size[0] * 72 + 2)
        self.assertTrue(expected_size[1] * 72 - 2 <= page_rect.upperRight[1] <= expected_size[1] * 72 + 2)

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
