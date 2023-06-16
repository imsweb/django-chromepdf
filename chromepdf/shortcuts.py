import warnings

from chromepdf.maker import ChromePdfMaker


def generate_pdf(html, pdf_kwargs=None, **kwargs):
    """
    Return the bytes of a PDF file that is generated from the HTML and pdf_kwargs passed in.

    html: A string
    pdf_kwargs: A dict containing any of the arguments accepted by Chrome's Page.printToPDF API.
    See the clean_pdf_kwargs() docstring below for a list of valid options.
    **kwargs: Lowercased settings such as chrome_path, and chromedriver_path. See conf.py's DEFAULT_SETTINGS dict.
    """

    return ChromePdfMaker(**kwargs).generate_pdf(html, pdf_kwargs)


def generate_pdf_url(url, pdf_kwargs=None, **kwargs):
    """
    NOTE: This function is DEPRECATED due to security concerns due to its ability to pull in any files on the server.
    Users should switch to using generate_pdf() as soon as possible.

    Return the bytes of a PDF file that is generated from the HTML and pdf_kwargs passed in.

    url: A url to load (may be local, too. EG: "file:///C:/Users/MyName/../../myfile.html")
    pdf_kwargs: A dict containing any of the arguments accepted by Chrome's Page.printToPDF API.
    See the clean_pdf_kwargs() docstring below for a list of valid options.
    **kwargs: Lowercased settings such as chrome_path, and chromedriver_path. See conf.py's DEFAULT_SETTINGS dict.

    If you have a local path that needs to be converted to a URI, you can import pathlib and call html_uri = pathlib.Path(mypath).as_uri()
    Sample use:

    from chromepdf import generate_pdf_url

    html_uri = "file:///C:/Users/myuser/Desktop/myfile.html"
    pdf_kwargs = {
        'paperFormat': 'A4',
        'marginTop': '2.5cm',
        'marginLeft': '2cm',
        'marginRight': '2cm',
        'marginBottom': '3.5cm',
        'displayHeaderFooter': True,
        'headerTemplate': '',
        'footerTemplate': '''
            <div style="font-size: 12px; width: 100%; padding: 0; padding-left: 2cm; padding-bottom: 1cm; margin: 0; ">
                Page <span class="pageNumber"></span> of <span class="totalPages"></span>
            </div>
        ''',
    }
    pdfbytes = generate_pdf_url(html_uri, pdf_kwargs)

    with open("myfile.pdf", 'wb') as file:
        file.write(pdfbytes)


    """

    return ChromePdfMaker(**kwargs).generate_pdf_url(url, pdf_kwargs)
