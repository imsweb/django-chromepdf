import string
from decimal import Decimal

# For more information, see: https://www.w3.org/TR/CSS2/syndata.html#length-units
# NOTE: All keys should be two chars long.
UNITS_PER_INCH = {
    'px': 96,  # these are "Reference Pixels" (defined by CSS standard as 96 DPI (.75 px/pt, and 72 pt/in = 96).
    'cm': 2.54,
    'mm': 25.4,
    'in': 1,
}
UNIT_STR_LENGTH = 2  # our parser expects all unit types to be two characters long ("in", "cm", etc)

# All values MUST be provided as integers and given in inches.
# These values will be passed to Page.PrintToPDF, which only accepts inches.
# same ones as supported  by PhantomJS, + ledger
# A good reference for these sizes (used for printers): https://doc.qt.io/archives/qt-5.10/qpagesize.html
PAPER_FORMATS = {
    'ledger': {'width': 17, 'height': 11},
    'legal': {'width': 8.5, 'height': 14},
    'letter': {'width': 8.5, 'height': 11},
    'tabloid': {'width': 11, 'height': 17},
    'a3': {'width': 11.69, 'height': 16.54},
    'a4': {'width': 8.26, 'height': 11.69},
    'a5': {'width': 5.83, 'height': 8.26},
}


def convert_to_inches(size):
    """
    Take a case-insensitive string consisting of a CSS length and return a float of that value in inches.
    If an int or float is passed in, then it is assumed to be an int and is returned as-is.
    If None is passed, return None (presumed that we're trying to "disable" the setting).
    """

    if size is None:
        return None
    elif isinstance(size, (int, float, Decimal)):  # inches
        return size
    elif isinstance(size, str) and len(size) > UNIT_STR_LENGTH:
        format_num = size[:-UNIT_STR_LENGTH]  # EG "2.5in" => "2.5"
        format_str = size[-UNIT_STR_LENGTH:].lower()  # EG "2.5in" => "in"
        # invalid unit type?
        if format_str not in UNITS_PER_INCH:
            raise ValueError('generate_pdf() cannot understand a length value of: "%s"' % str(size))
        # if this contains any whitespace, raise value error (not valid CSS)
        if any(c in string.whitespace for c in format_num):
            raise ValueError('generate_pdf() cannot understand a length value of: "%s"' % str(size))
        try:
            value = float(format_num)

            return value / UNITS_PER_INCH[format_str]  # convert to inches
        except ValueError:
            raise ValueError('generate_pdf() cannot understand a length value of: "%s"' % str(size))
    else:
        raise ValueError('generate_pdf() cannot understand a length value of: "%s"' % str(size))


def convert_to_unit(size, unit):
    """
    Take any int/float size value, and return an int/float of that value in the specified unit type.
    convert_to_unit('1in', 'cm') => 2.54
    """
    if unit not in UNITS_PER_INCH:
        raise ValueError(f'Invalid unit type: {unit}')
    return convert_to_inches(size) * UNITS_PER_INCH[unit]
