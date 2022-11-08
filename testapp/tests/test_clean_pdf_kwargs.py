from copy import deepcopy
from unittest.case import TestCase

from django.test.utils import override_settings

from chromepdf.conf import get_chromepdf_settings_dict
from chromepdf.pdfconf import DEFAULT_PDF_KWARGS, clean_pdf_kwargs, get_default_pdf_kwargs
from chromepdf.sizes import PAPER_FORMATS, convert_to_inches


class ChromePdfKwargsSettingsCopyTests(TestCase):

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'marginLeft': '5cm'}})
    def test_clean_pdf_kwargs_defaults_not_edited(self):
        """clean_pdf_kwargs() should NEVER result in updates to DEFAULT_PDF_KWARGS or the Django settings dict."""

        # get the initial defaults and django settings
        defaults_dict = deepcopy(DEFAULT_PDF_KWARGS)
        settings_dict = deepcopy(get_chromepdf_settings_dict()['PDF_KWARGS'])

        _new_settings = clean_pdf_kwargs(marginLeft='6cm')

        # make sure parse_settings() did not alter the defaults dict, but rather worked on a copy
        self.assertEqual(defaults_dict, deepcopy(DEFAULT_PDF_KWARGS))

        # make sure parse_settings() did not alter the django pdf_kwargs setting
        self.assertEqual(settings_dict, deepcopy(get_chromepdf_settings_dict()['PDF_KWARGS']))

    def test_clean_pdf_kwargs_options_not_edited(self):
        """clean_pdf_kwargs() should NEVER result in updates to an options dict passed in."""

        # first popped parameter (since not part of Chrome's API)
        options = {'margin': '11mm'}
        _kwargs = clean_pdf_kwargs(**options)
        self.assertEqual(1, len(options))

        # second popped parameter (since not part of Chrome's API)
        options = {'paperFormat': 'letter'}
        _kwargs = clean_pdf_kwargs(**options)
        self.assertEqual(1, len(options))


class ChromePdfKwargsTests(TestCase):

    def test_clean_pdf_kwargs_defaults(self):
        """Ensure the default values of clean_pdf_kwargs() are what we expect."""

        expected_defaults = get_default_pdf_kwargs()
        actual_defaults = clean_pdf_kwargs()

        # Test for correct keys
        self.assertEqual(set(expected_defaults.keys()), set(actual_defaults.keys()),
                         'clean_pdf_kwargs() had unexpected differences in its return keys.')

        # Test for correct values
        for k, v in expected_defaults.items():
            self.assertEqual(v, actual_defaults[k],
                             'clean_pdf_kwargs() had wrong default value: {k}={actual_defaults[k]}, expected: {v}')

    def test_clean_pdf_kwargs_invalid_keys(self):

        # a single bad key will cause a failure
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(badKey='1')

        # multiple bad keys. Error message should list all of them. sorted.
        with self.assertRaises(ValueError) as context:
            _kwargs = clean_pdf_kwargs(badKey2='2', badKey1='1')

        # Make sure the error message identifies the unrecognized arguments for easier debugging.
        self.assertEqual('Unrecognized pdf_kwargs passed to generate_pdf(): badKey1, badKey2', str(context.exception))

    def test_clean_pdf_kwargs_override_boolean_values(self):
        """For each of the four boolean parameters, test setting them to True, False, and truthy/falsey values."""

        boolean_kwargs = ('landscape', 'displayHeaderFooter', 'printBackground', 'ignoreInvalidPageRanges')
        truthy_values = (True, 1, 'nonemptystring')
        falsey_values = (False, 0, '', None)
        for param in boolean_kwargs:

            for testval in truthy_values:
                with self.subTest(param=param, testval=testval):
                    kwargs = clean_pdf_kwargs(**{param: testval})
                    self.assertEqual(kwargs[param], True)

            for testval in falsey_values:
                with self.subTest(param=param, testval=testval):
                    kwargs = clean_pdf_kwargs(**{param: testval})
                    self.assertEqual(kwargs[param], False)

    def test_clean_pdf_kwargs_override_scale(self):
        kwargs = clean_pdf_kwargs(scale=1)
        self.assertEqual(kwargs['scale'], 1)
        kwargs = clean_pdf_kwargs(scale=2)
        self.assertEqual(kwargs['scale'], 2)
        kwargs = clean_pdf_kwargs(scale=4.5)
        self.assertEqual(kwargs['scale'], 4.5)

        kwargs = clean_pdf_kwargs(scale='2')
        self.assertEqual(kwargs['scale'], 2)

        kwargs = clean_pdf_kwargs(scale='2.5')
        self.assertEqual(kwargs['scale'], 2.5)

        with self.assertRaises(TypeError):
            kwargs = clean_pdf_kwargs(scale='NotAnInt')

    def test_clean_pdf_kwargs_pagesizes(self):

        DEFAULTS = get_default_pdf_kwargs()

        # set the height, width=default
        kwargs = clean_pdf_kwargs(paperWidth=12)
        self.assertEqual(kwargs['paperWidth'], 12)
        self.assertEqual(kwargs['paperHeight'], DEFAULTS['paperHeight'])

        # set the width, height=default
        kwargs = clean_pdf_kwargs(paperHeight=12)
        self.assertEqual(kwargs['paperWidth'], DEFAULTS['paperWidth'])
        self.assertEqual(kwargs['paperHeight'], 12)

        # set width and height to inches
        kwargs = clean_pdf_kwargs(paperWidth=10.5, paperHeight=12.5)
        self.assertEqual(kwargs['paperWidth'], 10.5)
        self.assertEqual(kwargs['paperHeight'], 12.5)

        # set width and height to non-inches value (lowercase)
        kwargs = clean_pdf_kwargs(paperWidth='8cm', paperHeight='12cm')
        self.assertEqual(kwargs['paperWidth'], convert_to_inches('8cm'))
        self.assertEqual(kwargs['paperHeight'], convert_to_inches('12cm'))

        # set width and height to non-inches value (uppercase)
        kwargs = clean_pdf_kwargs(paperWidth='8CM', paperHeight='12CM')
        self.assertEqual(kwargs['paperWidth'], convert_to_inches('8cm'))
        self.assertEqual(kwargs['paperHeight'], convert_to_inches('12cm'))

        # set width and height to float inch string values
        kwargs = clean_pdf_kwargs(paperWidth='8.0in', paperHeight='12.0in')
        self.assertEqual(kwargs['paperWidth'], convert_to_inches(8))
        self.assertEqual(kwargs['paperHeight'], convert_to_inches(12))

        # raise ValueErrors for bad unit types
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperWidth='8zz')
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperHeight='8zz')
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperHeight='inin')
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperHeight='888')
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperHeight='')
        # disallow whitespace?
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperHeight='8 in')  # isn't valid CSS so don't allow it here.
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperHeight=' 8in')
        with self.assertRaises(ValueError):
            _kwargs = clean_pdf_kwargs(paperHeight='8in ')
        # type error (these cannot be None)
        with self.assertRaises(TypeError):
            _kwargs = clean_pdf_kwargs(paperHeight=None)
        with self.assertRaises(TypeError):
            _kwargs = clean_pdf_kwargs(paperWidth=None)

        # raise ValueError if paperFormat is not recognized
        with self.assertRaises(ValueError):
            kwargs = clean_pdf_kwargs(paperFormat='A9')

        # set a paperFormat (lowercase)
        kwargs = clean_pdf_kwargs(paperFormat='a4')
        self.assertTrue('paperFormat' not in kwargs)  # should have affected width and height, then be ditched.
        self.assertEqual(kwargs['paperWidth'], PAPER_FORMATS['a4']['width'])
        self.assertEqual(kwargs['paperHeight'], PAPER_FORMATS['a4']['height'])

        # set a paperFormat (uppercase)
        kwargs = clean_pdf_kwargs(paperFormat='A4')
        self.assertTrue('paperFormat' not in kwargs)  # should have affected width and height, then be ditched.
        self.assertEqual(kwargs['paperWidth'], PAPER_FORMATS['a4']['width'])
        self.assertEqual(kwargs['paperHeight'], PAPER_FORMATS['a4']['height'])

        # raise ValueError if paperFormat passed along with paperWidth and/or paperHeight
        with self.assertRaises(ValueError):
            kwargs = clean_pdf_kwargs(paperFormat='A4', paperWidth=10.5)
        with self.assertRaises(ValueError):
            kwargs = clean_pdf_kwargs(paperFormat='A4', paperHeight=12.5)
        with self.assertRaises(ValueError):
            kwargs = clean_pdf_kwargs(paperFormat='A4', paperWidth=10.5, paperHeight=12.5)

    def test_clean_pdf_kwargs_margins(self):

        DEFAULTS = get_default_pdf_kwargs()

        margin_kwargs = ('marginTop', 'marginBottom', 'marginLeft', 'marginRight')

        # test setting each margin individually
        for k in margin_kwargs:
            with self.subTest(k=k):
                kwargs = clean_pdf_kwargs(**{k: 2})
                self.assertEqual(kwargs[k], 2)  # overrides the one
                for k2 in margin_kwargs:
                    if k != k2:
                        self.assertEqual(kwargs[k2], DEFAULTS[k2])  # leaves others alone

        # set all margins to different values, in various formats
        kwargs = clean_pdf_kwargs(marginTop=3, marginBottom='2.5cm', marginLeft='10mm', marginRight='30px')
        self.assertEqual(kwargs['marginTop'], 3)
        self.assertEqual(kwargs['marginBottom'], convert_to_inches('2.5cm'))
        self.assertEqual(kwargs['marginLeft'], convert_to_inches('10mm'))
        self.assertEqual(kwargs['marginRight'], convert_to_inches('30px'))

        # set all four using the 'margin' kwarg:
        kwargs = clean_pdf_kwargs(margin='11mm')
        self.assertTrue('margin' not in kwargs)
        self.assertEqual(kwargs['marginTop'], convert_to_inches('11mm'))
        self.assertEqual(kwargs['marginBottom'], convert_to_inches('11mm'))
        self.assertEqual(kwargs['marginLeft'], convert_to_inches('11mm'))
        self.assertEqual(kwargs['marginRight'], convert_to_inches('11mm'))

        # set all four using margin, but override some as well
        kwargs = clean_pdf_kwargs(margin='11mm', marginTop='5mm', marginBottom='6mm')
        self.assertTrue('margin' not in kwargs)
        self.assertEqual(kwargs['marginTop'], convert_to_inches('5mm'))
        self.assertEqual(kwargs['marginBottom'], convert_to_inches('6mm'))
        self.assertEqual(kwargs['marginLeft'], convert_to_inches('11mm'))
        self.assertEqual(kwargs['marginRight'], convert_to_inches('11mm'))

        # cannot set margins to None
        for m in margin_kwargs:
            with self.subTest(m=m):
                with self.assertRaises(TypeError):
                    _kwargs = clean_pdf_kwargs(**{m: None})

    def test_clean_pdf_kwargs_templates(self):

        # just make sure the overrides get passed through.
        kwargs = clean_pdf_kwargs(headerTemplate='<div>Header</div>', footerTemplate='<div>Footer</div>')
        self.assertEqual(kwargs['headerTemplate'], '<div>Header</div>')
        self.assertEqual(kwargs['footerTemplate'], '<div>Footer</div>')

    def test_clean_pdf_kwargs_pageranges(self):

        # test int type
        kwargs = clean_pdf_kwargs(pageRanges=1)
        self.assertEqual(kwargs['pageRanges'], '1')

        # test valid string types
        kwargs = clean_pdf_kwargs(pageRanges='1-5, 8, 11-13')
        self.assertEqual(kwargs['pageRanges'], '1-5, 8, 11-13')

        # as of 1.1, we do NOT do any validation client-side. if we do, this would be a breaking change.
        kwargs = clean_pdf_kwargs(pageRanges='SDFGSDFGSDFG')
        self.assertEqual(kwargs['pageRanges'], 'SDFGSDFGSDFG')

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'marginTop': '8cm'}})
    def test_clean_pdf_kwargs_settings(self):
        """Make sure Django settings overrides are accounted for."""

        kwargs = clean_pdf_kwargs()
        self.assertEqual(kwargs['marginTop'], convert_to_inches('8cm'))

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'marginTop': '8cm', 'marginBottom': '7cm'}})
    def test_clean_pdf_kwargs_priority(self):
        """
        Ensure priority of overrides:
        keyword arguments > Django setting > hardcoded DEFAULT_PDF_KWARGS
        """

        kwargs = clean_pdf_kwargs(marginTop='9cm')
        self.assertEqual(kwargs['marginTop'], convert_to_inches('9cm'))  # overridden by keyword arg (overrides Django setting)
        self.assertEqual(kwargs['marginBottom'], convert_to_inches('7cm'))  # overridden by Django setting
        self.assertEqual(kwargs['marginLeft'], convert_to_inches('1cm'))  # DEFAULT_PDF_KWARGS value

    @override_settings(CHROMEPDF={'PDF_KWARGS': {'margin': '2cm'}})
    def test_clean_pdf_kwargs_priority2(self):
        """
        Ensure convenience Django settings still get overridden by subsetted keyword arguments.
        """

        kwargs = clean_pdf_kwargs(marginTop='3cm')
        self.assertEqual(kwargs['marginTop'], convert_to_inches('3cm'))  # overridden by keyword argument
        self.assertEqual(kwargs['marginBottom'], convert_to_inches('2cm'))  # overridden by Django setting
        self.assertEqual(kwargs['marginLeft'], convert_to_inches('2cm'))  # overridden by Django setting
        self.assertEqual(kwargs['marginRight'], convert_to_inches('2cm'))  # overridden by Django setting
