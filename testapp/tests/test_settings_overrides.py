from django.conf import settings  # @UnusedImport
from django.test.testcases import SimpleTestCase
from django.test.utils import override_settings

from chromepdf.conf import parse_settings
from chromepdf.pdfconf import clean_pdf_kwargs
from chromepdf.sizes import convert_to_inches

CHROME_PATH_SETTING_VAL = r'C://django/settings/path/to/my/chrome'
CHROMEDRIVER_PATH_SETTING_VAL = r'C://django/settings/path/to/my/chromedriver'

CHROME_PATH_KWARG_VAL = r'C://kwarg/override/path/to/my/chrome'
CHROMEDRIVER_PATH_KWARG_VAL = r'C://kwarg/override/path/to/my/chromedriver'

# assert all unique paths
assert CHROME_PATH_SETTING_VAL != CHROME_PATH_KWARG_VAL != CHROMEDRIVER_PATH_SETTING_VAL != CHROMEDRIVER_PATH_KWARG_VAL


@override_settings(CHROMEPDF={})
class TestParseSettings(SimpleTestCase):
    """Test the parse_settings() function, which combines kwarg overrides with the Django settings."""

    @override_settings()
    def test_parse_settings_defaults_no_chromepdf(self):
        """Test parse_settings() where defaults get used, and settings.CHROMEPDF does not exist."""

        # Yes, you can simulate the absense of a setting via @override_settings() and then del. See Django docs.
        # "You can also simulate the absence of a setting by deleting it after settings have been overridden."
        del settings.CHROMEPDF

        output = parse_settings()

        # compare to values of 'DEFAULT_SETTINGS'.
        # hardcode the values so tests will fail if defaults get changed by accident.
        self.assertEqual(4, len(output))
        self.assertEqual(output['chrome_path'], None)
        self.assertEqual(output['chromedriver_path'], None)
        self.assertEqual(output['chromedriver_downloads'], True)
        self.assertEqual(output['chrome_args'], [])

    @override_settings()
    def test_parse_settings_kwargs(self):
        """Test result of parse_settings() function, with only kwargs passed and settings.CHROMEPDF does not exist."""

        # Yes, you can simulate the absense of a setting via @override_settings() and then del. See Django docs.
        # "You can also simulate the absence of a setting by deleting it after settings have been overridden."
        del settings.CHROMEPDF

        output = parse_settings(chrome_path=CHROME_PATH_KWARG_VAL,
                                chromedriver_path=CHROMEDRIVER_PATH_KWARG_VAL,
                                chromedriver_downloads=False,
                                chrome_args=['--no-sandbox'])

        self.assertEqual(4, len(output))
        self.assertEqual(output.get('chrome_path'), CHROME_PATH_KWARG_VAL)
        self.assertEqual(output.get('chromedriver_path'), CHROMEDRIVER_PATH_KWARG_VAL)
        self.assertEqual(output.get('chromedriver_downloads'), False)
        self.assertEqual(output.get('chrome_args'), ['--no-sandbox'])

    @override_settings(CHROMEPDF={'CHROME_PATH': CHROME_PATH_SETTING_VAL,
                                  'CHROMEDRIVER_PATH': CHROMEDRIVER_PATH_SETTING_VAL,
                                  'CHROMEDRIVER_DOWNLOADS': False,
                                  'CHROME_ARGS': ['--no-sandbox']})
    def test_parse_settings_overridden_settings(self):
        """Test result of parse_settings() function, with overridden settings passed."""

        output = parse_settings()

        self.assertEqual(4, len(output))
        self.assertEqual(output['chrome_path'], CHROME_PATH_SETTING_VAL)
        self.assertEqual(output['chromedriver_path'], CHROMEDRIVER_PATH_SETTING_VAL)
        self.assertEqual(output['chromedriver_downloads'], False)
        self.assertEqual(output['chrome_args'], ['--no-sandbox'])

    @override_settings(CHROMEPDF={'CHROME_PATH': CHROME_PATH_SETTING_VAL,
                                  'CHROMEDRIVER_PATH': CHROMEDRIVER_PATH_SETTING_VAL,
                                  'CHROMEDRIVER_DOWNLOADS': True,
                                  'CHROME_ARGS': ['--no-sandbox']})
    def test_parse_settings_kwargs_and_overridden_settings(self):
        """
        Test result of parse_settings() function, with kwargs and overridden settings passed.
        Override values should take priority over django settings values.
        """

        output = parse_settings(chromedriver_downloads=False,
                                chrome_path=CHROME_PATH_KWARG_VAL,
                                chromedriver_path=CHROMEDRIVER_PATH_KWARG_VAL,
                                chrome_args=['yes-sandbox'])

        self.assertEqual(4, len(output))
        self.assertEqual(output.get('chrome_path'), CHROME_PATH_KWARG_VAL)
        self.assertEqual(output.get('chromedriver_path'), CHROMEDRIVER_PATH_KWARG_VAL)
        self.assertEqual(output.get('chromedriver_downloads'), False)
        self.assertEqual(output.get('chrome_args'), ['yes-sandbox'])

    @override_settings(CHROMEPDF={'CHROME_PATH': CHROME_PATH_SETTING_VAL,
                                  'CHROMEDRIVER_PATH': CHROMEDRIVER_PATH_SETTING_VAL,
                                  'CHROMEDRIVER_DOWNLOADS': True,
                                  'CHROME_ARGS': ['--no-sandbox']})
    def test_parse_settings_kwargs_and_overridden_settings_falsey(self):
        """
        Overridden values should take priority even if they are falsey.
        """

        output = parse_settings(chrome_path=None,
                                chromedriver_path=None,
                                chromedriver_downloads=False,
                                chrome_args=[])

        self.assertEqual(4, len(output))
        self.assertEqual(output.get('chrome_path'), None)
        self.assertEqual(output.get('chromedriver_path'), None)
        self.assertEqual(output.get('chromedriver_downloads'), False)
        self.assertEqual(output.get('chrome_args'), [])

    @override_settings(CHROMEPDF={'CHROME_PATH': CHROME_PATH_SETTING_VAL,
                                  'CHROMEDRIVER_PATH': CHROMEDRIVER_PATH_SETTING_VAL,
                                  'CHROME_ARGS': ['--no-sandbox']})
    def test_parse_settings_empty_paths(self):
        """Test result of parse_settings() function, where falsey values of the wrong type are converted to correct ones."""

        output = parse_settings(chrome_path='',
                                chromedriver_path='',
                                chromedriver_downloads=None,
                                chrome_args=None)

        # parsed values should be converted to None instead of ''
        self.assertEqual(4, len(output))
        self.assertEqual(output['chrome_path'], None)
        self.assertEqual(output['chromedriver_path'], None)
        self.assertEqual(output['chromedriver_downloads'], False)
        self.assertEqual(output['chrome_args'], [])


class TestSettingsOverridesPdfKwargs(SimpleTestCase):

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'margin': '2cm'}})
    def test_override_pdf_kwargs(self):
        """Test settings override of margin (should override the four default margins)"""

        defaults = clean_pdf_kwargs()
        self.assertEqual(convert_to_inches('2cm'), defaults['marginLeft'])
        self.assertEqual(convert_to_inches('2cm'), defaults['marginRight'])
        self.assertEqual(convert_to_inches('2cm'), defaults['marginTop'])
        self.assertEqual(convert_to_inches('2cm'), defaults['marginBottom'])

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'marginLeft': '2cm', 'marginRight': '3cm'}})
    def test_override_pdf_kwargs_three_way_margins(self):
        """
        pdf_kwargs should override everything
        settings' PDF_KWARGS should override only the true defaults.
        True defaults should be final fallback if no overrides were provided anywhere
        """

        pdf_kwargs = {'marginLeft': '3cm', 'marginBottom': '4cm'}
        cleaned = clean_pdf_kwargs(**pdf_kwargs)
        self.assertEqual(convert_to_inches('3cm'), cleaned['marginRight'])  # override in settings
        self.assertEqual(convert_to_inches('3cm'), cleaned['marginLeft'])  # override in pdf_kwargs (takes priority over settings)
        self.assertEqual(convert_to_inches('4cm'), cleaned['marginBottom'])  # override in pdf_kwargs
        self.assertEqual(convert_to_inches('1cm'), cleaned['marginTop'])  # true default (no overrides)

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'paperFormat': 'a5', 'paperWidth': 8.5}})
    def test_override_pdf_kwargs_conflict(self):
        """
        Raise exception if our settings contain pdf_kwargs that conflict.
        """

        with self.assertRaises(ValueError):
            pdf_kwargs = {}
            _cleaned = clean_pdf_kwargs(**pdf_kwargs)

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'paperFormat': 'a5'}})
    def test_override_pdf_kwargs_no_conflict(self):
        """
        Having a settings that contains a conflict with pdf_kwargs argument is okay (second takes priority).
        """

        pdf_kwargs = {'paperWidth': 8.5, 'paperHeight': 11}
        cleaned = clean_pdf_kwargs(**pdf_kwargs)
        self.assertEqual(8.5, cleaned['paperWidth'])
        self.assertEqual(11, cleaned['paperHeight'])
