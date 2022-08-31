
def command_line_interface(*args):
    """
    A method of generating PDF files from the command line. To execute, run:
    > python -m chromepdf.run --generate-pdf [args] [kwargs]
    """

    import argparse
    import os
    parser = argparse.ArgumentParser()

    group = parser.add_argument_group('group')
    group.add_argument("--generate-pdf", action='store_true', dest="generate_pdf", help='Will generate a PDF file. Followed by one or two args: The part to the input HTML file, and path to the output PDF file. EG: "--generate-pdf path/to/file.html path/to/file.pdf"')
    group.add_argument('paths', nargs='*')

    #parser.add_argument("--pdf-kwargs", dest="pdf_kwargs", help="A string that can JSON-decode to a pdf_kwargs dict.")

    parser.add_argument("--chrome-path", dest="chrome_path", help="Pass path to Chrome executable")
    parser.add_argument("--chromedriver-path", dest="chromedriver_path", help="Pass path to Chrome executable")
    parser.add_argument("--chromedriver-downloads", dest="chromedriver_downloads", type=int, choices=(0, 1), help='1 or 0, to indicate whether to use Chromedriver downloads or not.')
    parser.add_argument("--chrome-args", dest="chrome_args", help='A string of all arguments to pass to Chrome, separated by spaces.')

    namespace = parser.parse_args(*args)
    # print(namespace)
    if namespace.generate_pdf:
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

        # if namespace.outfile is None:
        #     outpath = os.path.splitext(inpath)[0] + '.pdf'
        # else:
        #     outpath = namespace.outfile

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
        # if namespace.pdf_kwargs is not None:
        #     try:
        #         import json
        #         pdf_kwargs = json.loads(namespace.pdf_kwargs)
        #     except json.JSONDecodeError:
        #         parser.error('--pdf-kwargs: must be a JSON dict encoded as a string')
        # assert isinstance(pdf_kwargs, dict), f'{pdf_kwargs} {type(namespace.pdf_kwargs)} {namespace.pdf_kwargs}'
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


if __name__ == '__main__':
    import sys
    command_line_interface(sys.argv[1:])
