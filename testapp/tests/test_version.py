import os
from unittest.case import TestCase

from chromepdf import __version__


class ChromePdfKwargsTests(TestCase):
    """
    Ensure the version in setup.py matches the one in chromepdf.__init__.__version__

    setup.py cannot import __version__ because it would try to import dependencies before it can install them.
    And we can't open setup.py because it's outside chromepdf.

    """

    def test_version_string(self):

        expected_string = f"version='{__version__}',"

        setup_py_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'setup.py')
        self.assertTrue(os.path.exists(setup_py_path))

        with open(setup_py_path, 'r') as f:
            data = f.read()

        self.assertTrue(expected_string in data)
