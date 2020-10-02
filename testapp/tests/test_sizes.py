from decimal import Decimal
from unittest.case import TestCase

from chromepdf.sizes import convert_to_inches, convert_to_unit


class ChromePdfKwargsTests(TestCase):

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
