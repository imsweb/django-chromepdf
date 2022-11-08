import os
import pathlib
import tempfile
from unittest.case import TestCase

from django.test.utils import tag

from chromepdf import generate_pdf, generate_pdf_url
from testapp.tests.utils import extractText


@tag('stresstest')
class GeneratePdfStressTests(TestCase):

    def test_generate_pdf_huge_pdfs(self):
        """Test outputting PDFs when the HTML is 1 MB."""

        html = '123456789 ' * ((1000 * 1000) // 10)  # 10 bytes * 1 MB = 1 MB

        # generate_pdf
        pdfbytes = generate_pdf(html)
        self.assertIsInstance(pdfbytes, bytes)
        extracted_text = extractText(pdfbytes).strip()
        self.assertEqual(1000 * 100, extracted_text.count('123456789'))

    def test_generate_pdf_url_huge_pdfs(self):

        html = '123456789 ' * ((1000 * 1000) // 10)  # 10 bytes * 1 MB = 1 MB

        # generate_pdf_url
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(html.encode('utf8'))  # 10* 100*1000 = 1 MB

                tempfile_uri = pathlib.Path(temp.name).as_uri()
                pdfbytes = generate_pdf_url(tempfile_uri)
                extracted_text = extractText(pdfbytes).strip()
                self.assertEqual(1000 * 100, extracted_text.count('123456789'))
        finally:
            os.remove(temp.name)
