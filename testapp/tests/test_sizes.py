from decimal import Decimal
from unittest.case import TestCase

from chromepdf.sizes import (PAPER_FORMATS, UNIT_STR_LENGTH, UNITS_PER_INCH,
                             convert_to_inches, convert_to_unit)


class ChromePdfKwargsTests(TestCase):

    def test_paperformat_sizes(self):
        """Make sure all paperFormat values are lowercased, and given in inches as ints/floats."""

        for k, v in PAPER_FORMATS.items():
            self.assertEqual(k, k.lower())
            self.assertIsInstance(v.get('width'), (int, float))
            self.assertIsInstance(v.get('height'), (int, float))

    def test_unit_types(self):
        """Make sure all unit types are lowercased, and have names of length 2, and types of int/float."""

        for k, v in UNITS_PER_INCH.items():
            self.assertIsInstance(k, str)
            self.assertEqual(k, k.lower())
            self.assertEqual(UNIT_STR_LENGTH, len(k))
            self.assertIsInstance(v, (int, float))

    def test_convert_return_types(self):
        """Return types must always be floats or ints (since they are JSON-serializable). Otherwise, Selenium will fail when creating JSON."""

        JSON_NUMERIC_TYPES = (int, float)

        self.assertIsInstance(convert_to_inches(1), JSON_NUMERIC_TYPES)
        self.assertIsInstance(convert_to_inches('1in'), JSON_NUMERIC_TYPES)
        self.assertIsInstance(convert_to_inches('.75in'), JSON_NUMERIC_TYPES)
        # Important! Decimal is NOT json-serializable. It must be converted to int/float
        self.assertIsInstance(convert_to_inches(Decimal('1.75')), JSON_NUMERIC_TYPES)

        self.assertIsInstance(convert_to_unit(1, 'in'), JSON_NUMERIC_TYPES)
        self.assertIsInstance(convert_to_unit('1in', 'in'), JSON_NUMERIC_TYPES)
        self.assertIsInstance(convert_to_unit('.75in', 'in'), JSON_NUMERIC_TYPES)
        # Important! Decimal is NOT json-serializable. It must be converted to int/float
        self.assertIsInstance(convert_to_unit(Decimal('1.75'), 'in'), JSON_NUMERIC_TYPES)

        # string lengths MUST provide a unit type.
        with self.assertRaises(ValueError):
            convert_to_inches('1')
        with self.assertRaises(ValueError):
            convert_to_unit('1', 'in')

    def test_unit_conversions(self):

        self.assertEqual(1, convert_to_inches('25.4mm'))
        self.assertEqual(1, convert_to_inches('2.54cm'))
        self.assertEqual(1, convert_to_inches('96px'))
        self.assertEqual(1, convert_to_inches('1in'))

        self.assertEqual(0.0394, round(convert_to_inches('1mm'), 4))
        self.assertEqual(0.3937, round(convert_to_inches('1cm'), 4))
        self.assertEqual(0.0104, round(convert_to_inches('1px'), 4))
        self.assertEqual(1, round(convert_to_inches('1in'), 4))

        self.assertEqual(25.4, convert_to_unit(1, 'mm'))
        self.assertEqual(2.54, convert_to_unit(1, 'cm'))
        self.assertEqual(96, convert_to_unit(1, 'px'))
        self.assertEqual(1, convert_to_unit(1, 'in'))

        self.assertEqual(25.4, convert_to_unit('96px', 'mm'))
        self.assertEqual(2.54, convert_to_unit('96px', 'cm'))
        self.assertEqual(96, convert_to_unit('96px', 'px'))
        self.assertEqual(1, convert_to_unit('96px', 'in'))

        # Allow decimal, int and float
        self.assertEqual(1.75, convert_to_inches(Decimal('1.75')))
        self.assertEqual(1.75, convert_to_inches(1.75))
        self.assertEqual(2, convert_to_inches(2))

        # <1 conversion
        self.assertEqual(0.75, convert_to_inches('0.75in'))  # leading zero
        self.assertEqual(0.75, convert_to_inches('.75in'))  # no leading zero
        self.assertEqual(0.75, convert_to_inches(Decimal('0.75')))
        self.assertEqual(0.75, convert_to_inches(Decimal('.75')))
        self.assertEqual(0.75, convert_to_inches(.75))

        # zero conversion (ensure no division by zero issues)
        self.assertEqual(0, convert_to_inches('0mm'))
        self.assertEqual(0, convert_to_inches('0in'))
        self.assertEqual(0, convert_to_inches(Decimal('0.0')))
        self.assertEqual(0, convert_to_inches(Decimal('0')))
        self.assertEqual(0, convert_to_inches(0))

        self.assertEqual(0, convert_to_unit('0mm', 'cm'))
        self.assertEqual(0, convert_to_unit('0in', 'cm'))
        self.assertEqual(0, convert_to_unit(0, 'cm'))
