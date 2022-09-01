from unittest import mock
from unittest.case import TestCase

from coverage.annotate import os

from chromepdf import __version__ as chromepdf_version


def mock_setup(*args, **kwargs):
    pass


class ChromePdfPyPITests(TestCase):
    """Test various functionality associated with deploying/releasing to PyPI."""

    @mock.patch('setuptools.setup', side_effect=mock_setup)
    def test_setup(self, setup_func):

        # setup file has correct version?
        from setup import get_version
        setup_version = get_version()
        self.assertEqual(setup_version, chromepdf_version)

        # readme contents make sense?
        readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'README.md')
        with open(readme_path, 'r', encoding='utf8') as f:
            readme_contents = f.read()
        self.assertGreater(len(readme_contents), 1)

        # setup has correct long description?
        from setup import _GITHUB_MASTER_ROOT, get_long_description
        setup_long_description = get_long_description()
        # relative github urls were expanded to absolute github urls for display on pypi? otherwise they would not work.
        self.assertIn(f'{_GITHUB_MASTER_ROOT}CHANGELOG.md', setup_long_description)
        self.assertEqual(setup_long_description.replace(_GITHUB_MASTER_ROOT, ''), readme_contents)
        # do not expand already-absolute urls?
        self.assertNotIn(f'{_GITHUB_MASTER_ROOT}https://', setup_long_description)

    def test_version(self):

        version_tuple = tuple(int(i) for i in chromepdf_version.split('.'))
        self.assertEqual(3, len(version_tuple))
        self.assertTrue(version_tuple[0] >= 1)
