from chromepdf.conf import get_chromepdf_settings_dict
from chromepdf.sizes import PAPER_FORMATS, convert_to_inches

# Specified in printToPDF API - https://chromedevtools.github.io/devtools-protocol/1-3/Page/#method-printToPDF
# These are the "TRUE" defaults.
# If no overrides are provided in Django's settings.CHROMEPDF['PDF_KWARGS'], and no pdf_kwargs are passed to render functions,
# Then these are the parameters that would be used and passed to Chrome.
# You do NOT need to call convert_to_inches() when overriding these values yourself.
DEFAULT_PDF_KWARGS = dict(
    landscape=False,
    displayHeaderFooter=False,
    printBackground=False,
    scale=1,
    paperWidth=convert_to_inches('8.5in'),
    paperHeight=convert_to_inches('11in'),
    marginTop=convert_to_inches('1cm'),
    marginLeft=convert_to_inches('1cm'),
    marginRight=convert_to_inches('1cm'),
    marginBottom=convert_to_inches('1cm'),
    pageRanges='',
    ignoreInvalidPageRanges=False,
    headerTemplate='',
    footerTemplate='',
)


def get_default_pdf_kwargs():
    """
    Return the default pdf_kwargs used for rendering a PDF in Chrome.
    Use the values specified in Django settings.CHROMEPDF['PDF_KWARGS'] if they exist.
    Otherwise, fallback to the `DEFAULT_PDF_KWARGS` above.
    """

    defaults = {}
    defaults.update(DEFAULT_PDF_KWARGS)  # make sure we're working on a copy of the settings.

    settings_pdf_kwargs = get_chromepdf_settings_dict().get('PDF_KWARGS', {})
    if settings_pdf_kwargs:
        # clean the overrides using the "true" defaults as defaults.
        # When we call the generate_pdf() functions, the resulting combined "defaults" will be treated as defaults.
        # This way, when we fall back on the defaults for any not-provided arguments,
        # we can be sure they are in a consistent format.
        overrides = clean_pdf_kwargs(_defaults=defaults, **settings_pdf_kwargs)
        defaults.update(overrides)

    return defaults


def clean_pdf_kwargs(**options):
    """
    Clean the pdf_kwargs into a format that Page.printToPDF accepts.
    Our defaults should match the default arguments of the Page.printToPDF API.
    For more information, see: https://chromedevtools.github.io/devtools-protocol/1-3/Page/#method-printToPDF

    :param scale: Scale of the PDF. Default 1.
    :param landscape: True to use landscape mode. Default False.

    :param displayHeaderFooter: True to display header and footer. Default False.
    :param headerTemplate: HTML containing the header for all pages. Default is an empty string.
        You may pass html tags with specific classes in order to insert values:
            * date: formatted print date
            * title: document title
            * url: document location
            * pageNumber: current page number
            * totalPages: total pages in the document
        For example, <span class="title"></span> would generate span containing the title.
    :param footerTemplate: HTML containing the footer for all pages. Default is an empty string.
        You may pass html tags with specific classes in order to insert values (same as above)
    :param printBackground: True to print background graphics. Default False.

    :param paperWidth: Width of the paper, in inches. Can also use some CSS string values, like "30cm". Default: 8.5
    :param paperHeight: Height of the paper, in inches. Can also use some CSS string values, like "30cm". Default: 11
    :param paperFormat: A string indicating a paper size format, such as "letter" or "A4". Case-insensitive.
        This will override paperWidth and paperHeight.
        Not part of Page.printToPDF API.  Provided for convenience.

    :param margin: Shortcut used to set all four margin values at once.
        Not part of Page.printToPDF API.  Provided for convenience.
    :param marginTop: Top margin. Default '1cm'
    :param marginBottom: Bottom margin. Default '1cm'.
    :param marginLeft: Left margin. Default '1cm'.
    :param marginRight: Right margin. Default '1cm'.

    :param pageRanges: String indicating page ranges to use. Example: '1-5, 8, 11-13'
    :param ignoreInvalidPageRanges: If True, will silently ignore invalid "pageRanges" values. Default False.

    :param _defaults: Internal-only. An optional dict of default parameter overrides that have already been 'cleaned'.

    :return: A dict containing an options dict that be used for Page.printToPDF
    """

    if '_defaults' in options:
        defaults = options.pop('_defaults')
    else:
        defaults = get_default_pdf_kwargs()

    try:
        scale = float(options.get('scale', defaults['scale']))  # can be int or float, or numeric string
    except ValueError:  # passed a character string?
        raise TypeError('You must pass a numeric value for the "scale" of the PDF.')

    landscape = bool(options.get('landscape', defaults['landscape']))

    displayHeaderFooter = bool(options.get('displayHeaderFooter', defaults['displayHeaderFooter']))
    headerTemplate = options.get('headerTemplate', defaults['headerTemplate'])
    footerTemplate = options.get('footerTemplate', defaults['footerTemplate'])
    printBackground = bool(options.get('printBackground', defaults['printBackground']))

    paperWidth = defaults['paperWidth']
    paperHeight = defaults['paperHeight']
    if 'paperFormat' in options:  # convenience option that's not part of Chrome's API
        if options['paperFormat'].lower() not in PAPER_FORMATS:
            raise ValueError('Unrecognized paper format: "%s"' % options['paperFormat'])
        if 'paperWidth' in options or 'paperHeight' in options:
            raise ValueError('Cannot pass a paperFormat at the same time as a paperWidth/paperHeight.')

        paperFormat = PAPER_FORMATS.get(options.pop('paperFormat').lower())  # pop it so we can validate options below
        paperWidth = paperFormat['width']
        paperHeight = paperFormat['height']
    else:
        if 'paperWidth' in options:
            paperWidth = convert_to_inches(options['paperWidth'])
        if 'paperHeight' in options:
            paperHeight = convert_to_inches(options['paperHeight'])

    if paperWidth is None:
        raise TypeError('You must set a paperWidth for this PDF.')
    if paperHeight is None:
        raise TypeError('You must set a paperHeight for this PDF.')

    marginTop = defaults['marginTop']
    marginBottom = defaults['marginBottom']
    marginLeft = defaults['marginLeft']
    marginRight = defaults['marginRight']

    # margin affects all four sides. margin in options will override default side-specific defaults.
    if 'margin' in options:
        margin = convert_to_inches(options.pop('margin'))
        marginTop = marginBottom = marginLeft = marginRight = margin

    # margin overrides for specific sides
    marginTop = convert_to_inches(options.get('marginTop', marginTop))
    marginBottom = convert_to_inches(options.get('marginBottom', marginBottom))
    marginLeft = convert_to_inches(options.get('marginLeft', marginLeft))
    marginRight = convert_to_inches(options.get('marginRight', marginRight))

    if marginTop is None:
        raise TypeError('You cannot set marginTop to None')
    if marginBottom is None:
        raise TypeError('You cannot set marginBottom to None')
    if marginLeft is None:
        raise TypeError('You cannot set marginLeft to None')
    if marginRight is None:
        raise TypeError('You cannot set marginRight to None')

    pageRanges = str(options.get('pageRanges', defaults['pageRanges']))
    ignoreInvalidPageRanges = bool(options.get('ignoreInvalidPageRanges', defaults['ignoreInvalidPageRanges']))
    # transferMode: not applicable.

#     preferCSSPageSize = options.get('preferCSSPageSize','')

    # the actual dict that we will pass to Chrome (convenience kwargs like margin and paperFormat are removed)
    parameters = dict(
        scale=scale,
        landscape=landscape,
        #         preferCSSPageSize=preferCSSPageSize, # too new, causes error

        displayHeaderFooter=displayHeaderFooter,
        headerTemplate=headerTemplate,
        footerTemplate=footerTemplate,
        printBackground=printBackground,

        paperWidth=paperWidth,
        paperHeight=paperHeight,

        marginTop=marginTop,
        marginBottom=marginBottom,
        marginLeft=marginLeft,
        marginRight=marginRight,

        pageRanges=pageRanges,
        ignoreInvalidPageRanges=ignoreInvalidPageRanges,
    )

    # check for bad options
    parameters_keys = set(parameters.keys())
    options_keys = set(options.keys())
    if not options_keys.issubset(parameters_keys):
        raise ValueError('Unrecognized pdf_kwargs passed to generate_pdf(): %s' % (', '.join(options_keys - parameters_keys)))

    return parameters
