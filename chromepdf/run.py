
def chromepdf_run(*args):
    """
    A method of generating PDF files from the command line. To execute, run:
    > python -m chromepdf generate-pdf [args] [kwargs]
    """

    import argparse
    import os
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help='You may call the command "generatepdf"', dest='command')

    # For now, we only have one sub-command: generatepdf.
    # Other sub-commands may be added in the future
    genpdf_parser = subparsers.add_parser('generate-pdf', help='Will generate a PDF file. Followed by one or two args: The part to the input HTML file, and path to the output PDF file. EG: "--generate-pdf path/to/file.html path/to/file.pdf"')
    genpdf_parser.add_argument('paths', nargs='*')

    genpdf_parser.add_argument("--pdf-kwargs-json", dest="pdf_kwargs_json", help="Path to a JSON file whose contents can decode to a pdf_kwargs dict.")

    genpdf_parser.add_argument("--chrome-path", dest="chrome_path", help="Pass path to Chrome executable")
    genpdf_parser.add_argument("--chromedriver-path", dest="chromedriver_path", help="Pass path to Chrome executable")
    genpdf_parser.add_argument("--chromedriver-downloads", dest="chromedriver_downloads", type=int, choices=(0, 1), help='1 or 0, to indicate whether to use Chromedriver downloads or not.')
    genpdf_parser.add_argument("--chrome-args", dest="chrome_args", help='A string of all arguments to pass to Chrome, separated by spaces.')

    namespace = parser.parse_args(*args)
    # print(namespace)

    if namespace.command == 'generate-pdf':
        if namespace.paths is None or len(namespace.paths) == 0:
            parser.error('--generate-pdf: requires one or two path arguments for an infile and optional outfile.')

        if len(namespace.paths) == 1:
            inpath = namespace.paths[0]
            outpath = os.path.splitext(inpath)[0] + '.pdf'
        elif len(namespace.paths) == 2:
            inpath, outpath = namespace.paths
        else:
            parser.error('--generate-pdf: requires one or two path arguments for an infile and optional outfile.')

        #inpath = namespace.infile
        if not os.path.exists(inpath):
            parser.error(f'--generate-pdf: could not find input html file: "{inpath}"')

        with open(inpath, 'r', encoding='utf8') as f:
            html_str = f.read()

        kwargs = {}
        if namespace.chrome_path is not None:
            kwargs['chrome_path'] = namespace.chrome_path
        if namespace.chromedriver_path is not None:
            kwargs['chromedriver_path'] = namespace.chromedriver_path
        if namespace.chromedriver_downloads is not None:
            kwargs['chromedriver_downloads'] = bool(namespace.chromedriver_downloads)
        if namespace.chrome_args is not None:
            kwargs['chrome_args'] = namespace.chrome_args.split()

        pdf_kwargs = None
        if namespace.pdf_kwargs_json is not None:
            if not os.path.exists(namespace.pdf_kwargs_json):
                parser.error(f'--generate-pdf: could not find input pdf-kwargs-json file: "{namespace.pdf_kwargs_json}"')
            try:
                import json
                with open(namespace.pdf_kwargs_json, 'r', encoding='utf8') as f:
                    data = f.read()
                    pdf_kwargs = json.loads(data)
                if not isinstance(pdf_kwargs, dict):
                    parser.error('--pdf-kwargs-json: must be a path to file containing a JSON dict encoded as a string')
            except json.JSONDecodeError:
                parser.error('--pdf-kwargs-json: must be a path to file containing a JSON dict encoded as a string')

        from .shortcuts import generate_pdf
        pdf_bytes = generate_pdf(html_str, pdf_kwargs, **kwargs)
        outpath_dir = os.path.dirname(outpath)
        os.makedirs(outpath_dir, exist_ok=True)
        with open(outpath, 'wb') as f:
            f.write(pdf_bytes)

    else:
        parser.print_help()
        # 'Unix programs generally use 2 for command line syntax errors and 1 for all other kind of errors.'
        # If execution failed to run a reasonable task with command, return an error response.
        exit(2)
