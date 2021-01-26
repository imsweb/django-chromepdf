"""
testapp.tests.utils
Utility functions for assisting with unit tests.
"""

import tempfile
from io import BytesIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage


def extractText(pdfbytes):
    """Use pdfminer to take a pdf file-like-object/stream and return its text as a str."""

    fp = BytesIO(pdfbytes)

    retstr = BytesIO()
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
    """Create a temporary file with byte/str contents, and then close it."""

    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode('utf8')
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(file_bytes)  # 10 bytes
    temp.close()  # close it, so it can be copied from for opens
    return temp
