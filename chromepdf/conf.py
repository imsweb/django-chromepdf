DEFAULT_SETTINGS = {
    'CHROME_PATH': None,
    'CHROMEDRIVER_PATH': None,
    'CHROMEDRIVER_DOWNLOADS': True,
    # also, PDF_KWARGS, but it's handled differently
    'CHROME_ARGS': [],
    'USE_SELENIUM': None,
}


def get_chromepdf_settings_dict():
    """
    Return a Django's settings.CHROMEPDF dict. Return empty dict if not found or Django not installed.
    For our sanity, this should be the ONLY place within the chromepdf app that we import from Django.
    This way, the library should work even if Django is not installed (except with its settings ignored).
    """
    try:
        from django.conf import settings
        return getattr(settings, 'CHROMEPDF', {})
    except Exception:
        # catches ImportError and ModuleNotFoundError, and potentially Django's ImproperlyConfigured.
        # But we can't explitly name that here since Django might not be installed. So, use a general Exception.
        return {}


def parse_settings(**overrides):
    """
    Return a dict of lowercased DEFAULT_SETTINGS based on combination of defaults, Django settings, and overrides.
    Priority: keyword overrides > Django settings > DEFAULT_SETTINGS
    """

    output = {}
    chromepdf_settings = get_chromepdf_settings_dict()

    # iterate over expected setting names
    for k, defaultval in DEFAULT_SETTINGS.items():
        k_lower = k.lower()
        if k_lower in overrides:
            output[k_lower] = overrides[k_lower]  # get kwarg
        else:
            output[k_lower] = chromepdf_settings.get(k, defaultval)  # get Django setting, OR default value

        # convert falsey values to more appropriate ones.
        if k == 'CHROMEDRIVER_DOWNLOADS':  # boolean settings
            if output[k_lower] is None:
                output[k_lower] = False
        elif k == 'CHROME_ARGS':
            if output[k_lower] is None:
                output[k_lower] = []
            elif isinstance(output[k_lower], str):
                # Prevent passing individual characters in str to Chrome as args. Silent, and unexpected behavior.
                raise TypeError('The chrome_args/CHROME_ARGS parameter/setting must be an iterable of strings.')
        else:  # path settings
            if output[k_lower] == '':
                output[k_lower] = None

    return output
