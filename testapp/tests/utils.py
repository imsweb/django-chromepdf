"""
testapp.tests.utils
Utility functions for assisting with unit tests.
"""

import os
import tempfile
from io import BytesIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage


def findChromePath():
    """
    Check for a working path to a Google Chrome instance and return it. Raise Exception if none found.
    Use this in all unit tests whenever a valid Chrome path instance is needed.
    """

    chrome_paths = [
        # Windows
        'chrome.exe',  # CWD
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        # MacOS
        r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        # Linux
        'google-chrome',  # CWD
        r'/usr/bin/google-chrome',
    ]

    for p in chrome_paths:
        if os.path.exists(p):
            return os.path.abspath(p)  # abs path so OS relies on THE path we want, not on $PATH's precedence.

    raise RuntimeError('findChromePath() could not find a Google Chrome instance.')


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
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(file_bytes)
    return temp


class MockCompletedProcess:
    """Class for mocking a CompletedProcess with specific output returned by subprocess.run()."""

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout.encode('utf8') if isinstance(stdout, str) else stdout
        self.stderr = stderr.encode('utf8') if isinstance(stderr, str) else stderr
