import os
import pathlib
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
        path = os.path.abspath('contents.html')
        try:
            with open(path, 'wb') as f:
                f.write(html.encode('utf8'))

            tempfile_uri = pathlib.Path(path).as_uri()
            pdfbytes = generate_pdf_url(tempfile_uri)
            # with open('contents.pdf','wb') as f:
            #     f.write(pdfbytes)
            extracted_text = extractText(pdfbytes).strip()
            # with open('contents.txt','w',encoding='utf8') as f:
            #     f.write(f'Contents: {extracted_text}')
            self.assertEqual(1000 * 100, extracted_text.count('123456789'))
        finally:
            os.remove(path)
