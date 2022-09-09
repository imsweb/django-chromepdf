# ChromePDF

## Overview

ChromePDF is a small Python 3 library that uses [Selenium](https://pypi.org/project/selenium/) and Google Chrome to convert HTML into a PDF. This is accomplished by using Chrome's `Page.printToPDF` DevTools command.

ChromePDF provides a function that accepts an html string, plus a dict of page parameters, and other settings, and returns the bytes containing a PDF:

```
pdf_bytes = generate_pdf(html_string, pdf_kwargs, **kwargs)
```

As of version 1.4, ChromePDF can also be run from the command line.

```
python -m chromepdf generate-pdf --chrome-path=/usr/bin/google-chrome path/to/input.html path/to/output.pdf
```

Because it renders via Chrome, it supports a wide range of CSS and HTML tags that should display the same as if you used Chrome to view the HTML itself.

ChromePDF can take advantage of [Django](https://pypi.org/project/Django/) settings for configuration, but Django is not a required dependency.

Official ChromePDF releases [are available on PyPI](https://pypi.org/project/django-chromepdf/).

## Installation

**1. Install ChromePDF via pip.**

The latest version can be installed via PyPI. This will also install Selenium, the only direct dependency (Selenium versions 3 and 4 are supported; 3 will be used if already present, otherwise will install 4). 

You may view the [Changelog](CHANGELOG.md) for a list of all ChromePDF version changes. ChromePDF uses [semantic versioning](https://semver.org/) for its release numbering. You are encouraged to pin your requirements to a Major.Minor version in a manner that will also receive Bugfix updates like so:
```
pip install django-chromepdf~=1.4.0
```

**2. Set the location of your Chrome executable.** This can be done in one of two ways:

* In your Django settings, set `CHROMEPDF['CHROME_PATH']` to the full path of the executable (E.G., `r'C:\Program Files (x86)\Google\...\chrome.exe'`)
* OR, pass `chrome_path` as a keyword argument to the `generate_pdf()` function.

## About Chromedrivers

A chromedriver executable is necessary to interface between Selenium and Chrome. ChromePDF will automatically check the version of your Chrome binary and download the required chromedriver [from the Chrome website](https://chromedriver.chromium.org/downloads) if it doesn't exist, into your `site-packages/chromepdf/chromedrivers/` folder. If the Chrome binary ever gets upgraded, ChromePDF will realize this and download the required driver for it.

You may disable these automatic downloads in the following way:
* In your Django settings, set `CHROMEPDF['CHROMEDRIVER_DOWNLOADS']` to False
* OR, pass a `chromedriver_downloads=False` argument to `generate_pdf()`

You may also specify a chromedriver path manually. This is recommended if you disable downloads:
* In your Django settings, set `CHROMEPDF['CHROMEDRIVER_PATH']` to the full path of the executable (E.G., `r'C:\Users\myuser\...\chromedriver_win32\chromedriver.exe'`)
* OR, pass a `chromedriver_path` argument to `generate_pdf()` containing the path.
* OR, if both of the above are not set, and you've disabled downloads, and if your chromedriver is in your `PATH` environment variable, then Selenium should be able to find it automatically.

## Example: `generate_pdf()`
Note: `generate_pdf()` cannot include external files including CSS. You must include all your CSS within `<style>` tags or as inline styles.

```python
# NOTE: This example assumes that you've set Django's settings.CHROMEPDF['CHROME_PATH'] = '(path to your Chrome instance)'
from chromepdf import generate_pdf 

with open('myfile.html','r') as f:
    html_string = f.read()
             
pdf_kwargs = {
    'paperFormat': 'A4',
    'marginTop': '2.5cm',
    'marginLeft': '2cm',
    'marginRight': '2cm',
    'marginBottom': '3.5cm',
    'displayHeaderFooter': True,
    'headerTemplate': '',
    'footerTemplate': '''
        <div style='font-size: 12px; width: 100%; padding: 0; padding-left: 2cm; padding-bottom: 1cm; margin: 0; '>
            Page <span class='pageNumber'></span> of <span class='totalPages'></span>
        </div>
    ''',
}
pdf_bytes = generate_pdf(html_string, pdf_kwargs)

with open('myfile.pdf', 'wb') as file:
    file.write(pdf_bytes)
```

## Example: Command-Line Usage
ChromePDF can generate PDFs from the command-line. This method will not rely on Django settings. Example syntax:
```
# Convert file.html into file.pdf and place in the same directory
python -m chromepdf generate-pdf path/to/file.html [kwargs]

# Convert file.html and place the output PDF file at a specific path.
python -m chromepdf generate-pdf path/to/file.html path/to/output.pdf [kwargs]
```
Keyword arguments for command-line usage are almost identical to `generate_pdf()` keyword arguments:
```
--chrome-path=path/to/google-chrome
--chromedriver-path=path/to/chromedriver
--chromedriver-downloads=0 # 0 or 1
--chrome-args="--arg1 --arg2" # Always use quotes to avoid misinterpreting as commands. 
--pdf-kwargs-json=path/to/file.json # JSON file containing a dict of values to pass to pdf_kwargs
```
The recommended usage is to pass a `--chrome-path`, and let ChromePDF handle the chromedriver downloads automatically.
```
python -m chromepdf generate-pdf --chrome-path=/usr/bin/google-chrome path/to/file.html path/to/output.pdf
```
The command will have a return code of zero on success, and nonzero on failure.

## Django Settings

You can specify default settings in your Django settings file, if desired, via a `CHROMEPDF` settings. Anything passed via the `pdf_kwargs` argument will override the `PDF_KWARGS` settings.
```python
# settings.__init__.py

CHROMEPDF = {
    'CHROME_PATH': r'C:\Program Files (x86)\Google\...\chrome.exe',
    'CHROME_ARGS': [], # Optional list of command-line argument strings to pass to Chrome when rendering a PDF.
    'CHROMEDRIVER_PATH': None, # will rely on downloads instead
    'CHROMEDRIVER_DOWNLOADS': True, # automatically download the correct chromedriver for the chrome path
    'PDF_KWARGS': {
        'paperFormat': 'A4',
        'marginTop': '2.5cm',
        'marginLeft': '2cm',
        'marginRight': '2cm',
        'marginBottom': '3.5cm',
    }
}
```


## PDF_KWARGS Options

The `pdf_kwargs` argument to `generate_pdf()` lets you specify all the arguments for Chrome's `Page.printToPDF` API. Its API can be viewed here:

[Page.printToPDF API](https://chromedevtools.github.io/devtools-protocol/1-3/Page/#method-printToPDF) (url is funky. If you get a 404, try reloading/refreshing)

Some shortcut parameters are provided by `generate_pdf()` for convenience. Here is a list of all the options:

Layout:
*  **scale**: Scale of the PDF. Default `1`.
*  **landscape**: `True` to use landscape mode. Default `False`.

Page Dimensions:
*  **paperWidth**: Width of the paper, in inches. Can also use some CSS string values, like `'30cm'`. Default: `8.5`
*  **paperHeight**: Height of the paper, in inches. Can also use some CSS string values, like `'30cm'`. Default: `11`
*  **paperFormat**: A string indicating a paper size format, such as `'letter'` or `'A4'`. Case-insensitive. This will override `paperWidth` and `paperHeight`. Not part of `Page.printToPDF` API.  Provided for convenience.

Content:
*  **displayHeaderFooter**: `True` to display header and footer. Default `False`.
*  **headerTemplate**: HTML containing the header for all pages. Default is an empty string. You may pass html tags with specific classes in order to insert values. For example, `<span class='title'></span>` would insert the the title.
   * date: formatted print date 
   * title: document title 
   * url: document location 
   * pageNumber: current page number 
   * totalPages: total pages in the document 
* **footerTemplate**: HTML containing the footer for all pages. Default is an empty string. You may pass html tags with specific classes in order to insert values (same as above)
* **printBackground**: `True` to print background graphics. Default `False`.

Margins:
*  **margin**: Shortcut used to set all four margin values at once. Not part of `Page.printToPDF` API.  Provided for convenience.
*  **marginTop**: Top margin. Default: `'1cm'`
*  **marginBottom**: Bottom margin. Default: `'1cm'`
*  **marginLeft**: Left margin. Default: `'1cm'`
*  **marginRight**: Right margin. Default: `'1cm'`

Page Ranges:
*  **pageRanges**: String indicating page ranges to use. Example: `'1-5, 8, 11-13'`
*  **ignoreInvalidPageRanges**: If `True`, will silently ignore invalid 'pageRanges' values. Default `False`.

