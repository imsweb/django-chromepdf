import importlib
import io
import json
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
from unittest.case import TestCase

from django.conf import settings

import chromepdf
from chromepdf.run import chromepdf_run
from chromepdf.webdrivers import _get_chromedriver_environment_path
from testapp.tests.utils import extractText, findChromePath

# whichever python exe is running the tests, use the same one to run the commands.
PY_EXE = sys.executable


def subprocess_run(args, **kwargs):
    """
    Subprocess run shortcut that works in Python 3.6 (doesn't support capture_output=True)
    """

    # redundant. will ensure coverage will detect lines covered within chromepdf_run()
    # this is ugly, but easier than dealing with coverage correctly handling subprocess calls
    # and triggering false flag suspicious activity antivirus warnings...
    try:
        with mock.patch('chromepdf.shortcuts.generate_pdf') as m:
            m.side_effect = Exception('mock exception')  # raise exception, do not return files.
            m.return_value = b'12345'
            with redirect_stdout(io.StringIO()):
                with redirect_stderr(io.StringIO()):
                    chromepdf_run(args[3:])  # skip "python -m chromepdf" calls
    except BaseException:  # catch exception, systemexit, parse errors too
        pass

    # subprocess call that actually runs tests
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)  # pylint: disable=subprocess-run-check)
    return p


class CommandLineTests(TestCase):
    """Test generating PDFs via the command line."""

    @classmethod
    def setUpClass(cls):
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    def setUp(self):
        # delete files between tests so tests do not interfere
        for filename in os.listdir(settings.TEMP_DIR):
            file_path = os.path.join(settings.TEMP_DIR, filename)
            os.remove(file_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.TEMP_DIR)

    def test_main(self):
        """Test calling chrome.pdf.__main__, the entry point."""

        # "python -m chromepdf" causes sys.argv to be manipulated into something like this
        # by the time it reaches chromepdf.__main__
        argv = ['path/to/chromepdf/__main__.py', 'generate-pdf', 'input.html']

        from chromepdf import __main__
        with mock.patch.object(sys, 'argv', argv):
            with mock.patch('chromepdf.run.chromepdf_run') as f:
                __main__.main()
                f.assert_called_with(['generate-pdf', 'input.html'])

    def test_run_no_args(self):
        """Should display help text with error returncode"""

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf'])  # pylint: disable=subprocess-run-check
        self.assertIn('usage:', proc.stdout.decode('utf8'))  # dispalys help text?
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(2, proc.returncode)

    def test_run_help(self):
        """Should display help text without error returncode"""

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', '--help'])  # pylint: disable=subprocess-run-check
        self.assertIn('usage:', proc.stdout.decode('utf8'))  # dispalys help text?
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(0, proc.returncode)

    def test_generate_pdf_error_bad_subcommand(self):
        """Should display an error if an unfamiliar subcommand is given"""

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'bad-subcommand'])  # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn('error: argument command: invalid choice:', proc.stderr.decode('utf8'))  # dispalys help text?
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_error_no_args(self):
        """Should display an error about the subcommand 'generate-pdf'"""

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf'])  # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn('generate-pdf: requires one or two path arguments', proc.stderr.decode('utf8'))  # dispalys help text?
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_error_too_many_args(self):
        """Should display an error re: the number of arguments."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath, inpath, inpath])  # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn('generate-pdf: requires one or two path arguments', proc.stderr.decode('utf8'))  # dispalys help text?
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_error_missing_input_file(self):
        """Should display an error re: the number of arguments."""

        inpath = os.path.join(settings.TEMP_DIR, 'file-not-found.html')

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath])  # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn('generate-pdf: could not find input html file: ', proc.stderr.decode('utf8'))  # dispalys help text?
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_inpath(self):
        """Generate a PDF where only the inpath is provided."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html.rev1.html')  # ensure outfile name only replaces final '.html'
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(0, proc.returncode)

        expected_outpath = os.path.join(settings.TEMP_DIR, 'input.html.rev1.pdf')  # only replaces last suffix
        self.assertTrue(os.path.exists(expected_outpath))
        with open(expected_outpath, 'rb') as f:
            pdf_bytes = f.read()

        self.assertEqual(1, extractText(pdf_bytes).count(html))

    def test_generate_pdf_inpath_no_ext(self):
        """Generate a PDF where only the inpath is provided and has no extension."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'inputhtml')  # ensure outfile name only replaces final '.html'
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(0, proc.returncode)

        expected_outpath = os.path.join(settings.TEMP_DIR, 'inputhtml.pdf')  # suffix is appended
        self.assertTrue(os.path.exists(expected_outpath))
        with open(expected_outpath, 'rb') as f:
            pdf_bytes = f.read()

        self.assertEqual(1, extractText(pdf_bytes).count(html))

    def test_generate_pdf_inpath_cwd(self):
        """Generate a PDF where only the inpath is provided and already located in the current working directory."""

        # Test doing it on a file that's already in the current working directory
        # This could impact the mkdirs() command, which would fail if run on a path like ''

        html = 'One Word'
        inpath = os.path.join('input.rev2.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(0, proc.returncode)

        outpath = inpath.replace('.html', '.pdf')
        self.assertTrue(os.path.exists(outpath))
        with open(outpath, 'rb') as f:
            pdf_bytes = f.read()

        self.assertEqual(1, extractText(pdf_bytes).count(html))

        if os.path.exists(inpath):
            os.remove(inpath)
        if os.path.exists(outpath):
            os.remove(outpath)

    def test_generate_pdfkwargs_file_not_found(self):
        """Generate a PDF where --pdf-kwargs-json file is missing."""

        inpath = os.path.join(settings.TEMP_DIR, 'input.rev1.html')
        outpath = inpath.replace('.html', '.pdf')

        if os.path.exists(outpath):
            os.remove(outpath)

        html = 'One Word'
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)

        pdf_kwargs_json_path = os.path.join(settings.TEMP_DIR, 'pdf_kwargs.json')
        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath, f'--pdf-kwargs-json={pdf_kwargs_json_path}'])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn(b'generate-pdf: could not find input pdf-kwargs-json file', proc.stderr)
        self.assertEqual(2, proc.returncode)
        self.assertFalse(os.path.exists(outpath))

    def test_generate_pdfkwargs_invalid_json(self):
        """Generate a PDF where --pdf-kwargs-json does not contain valid json."""

        inpath = os.path.join(settings.TEMP_DIR, 'input.rev1.html')
        outpath = inpath.replace('.html', '.pdf')

        if os.path.exists(outpath):
            os.remove(outpath)

        html = 'One Word'
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        pdf_kwargs_json_path = os.path.join(settings.TEMP_DIR, 'pdf_kwargs.json')
        with open(pdf_kwargs_json_path, 'w', encoding='utf8') as f:
            f.write("{ bad json")

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath, f'--pdf-kwargs-json={pdf_kwargs_json_path}'])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn(b'--pdf-kwargs-json: must be a path to a file containing a JSON dict {} of key-value pairs. The JSON in this file is not valid JSON.', proc.stderr)
        self.assertEqual(2, proc.returncode)
        self.assertFalse(os.path.exists(outpath))

    def test_generate_pdfkwargs_json_not_dict(self):
        """Generate a PDF where --pdf-kwargs-json contains a non-dict json-encoded value."""

        inpath = os.path.join(settings.TEMP_DIR, 'input.rev1.html')
        outpath = inpath.replace('.html', '.pdf')

        if os.path.exists(outpath):
            os.remove(outpath)

        html = 'One Word'
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        pdf_kwargs = ['marginWrong']  # this is not a valid pdf_kwargs setting. PDF generation should fail.
        pdf_kwargs_json_path = os.path.join(settings.TEMP_DIR, 'pdf_kwargs.json')
        with open(pdf_kwargs_json_path, 'w', encoding='utf8') as f:
            f.write(json.dumps(pdf_kwargs))

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath, f'--pdf-kwargs-json={pdf_kwargs_json_path}'])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn(b'--pdf-kwargs-json: must be a path to a file containing a JSON dict {} of key-value pairs. The JSON in this file is a different data type.', proc.stderr)
        self.assertEqual(2, proc.returncode)
        self.assertFalse(os.path.exists(outpath))

    def test_generate_pdfkwargs_bad_values(self):
        """Generate a PDF where --pdf-kwargs-json contains pdf kwargs that are not recognized."""

        inpath = os.path.join(settings.TEMP_DIR, 'input.rev1.html')
        outpath = inpath.replace('.html', '.pdf')

        if os.path.exists(outpath):
            os.remove(outpath)

        html = 'One Word'
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        pdf_kwargs = {'marginWrong': '1in'}  # this is not a valid pdf_kwargs setting. PDF generation should fail.
        pdf_kwargs_json_path = os.path.join(settings.TEMP_DIR, 'pdf_kwargs.json')
        with open(pdf_kwargs_json_path, 'w', encoding='utf8') as f:
            f.write(json.dumps(pdf_kwargs))

        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath, f'--pdf-kwargs-json={pdf_kwargs_json_path}'])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn(b'ValueError: Unrecognized pdf_kwargs passed to generate_pdf()', proc.stderr)
        self.assertEqual(1, proc.returncode)
        self.assertFalse(os.path.exists(outpath))

    def test_generate_pdf_inpath_outpath(self):
        """Generate a PDF where the inpath AND outpath are provided."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        outpath = os.path.join(settings.TEMP_DIR, 'output.pdf')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess_run([PY_EXE, '-m', 'chromepdf', 'generate-pdf', inpath, outpath])   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(0, proc.returncode)

        self.assertTrue(os.path.exists(outpath))
        with open(outpath, 'rb') as f:
            pdf_bytes = f.read()

        self.assertEqual(1, extractText(pdf_bytes).count(html))

    def test_generate_pdf_all_kwargs(self):
        """
        Pass all kwargs through run interface. Make sure they generate a PDF.
        Also make sure they all arguments arrive at generate_pdf() with the expected values.
        """

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        outpath = inpath.replace('.html', '.pdf')

        chrome_path = findChromePath()
        chromedriver_path = _get_chromedriver_environment_path()
        chrome_args_list = ['--no-sandbox', '--null']
        chrome_args = ' '.join(chrome_args_list)
        pdf_kwargs = {'margin': 1, 'marginLeft': '1in'}
        pdf_kwargs_json_path = os.path.join(settings.TEMP_DIR, 'pdf_kwargs.json')
        with open(pdf_kwargs_json_path, 'w', encoding='utf8') as f:
            f.write(json.dumps(pdf_kwargs))

        args_original = [
            PY_EXE,
            '-m',
            'chromepdf',
            'generate-pdf',
            inpath,
            outpath,
            f'--chrome-path={chrome_path}',
            f'--chromedriver-path={chromedriver_path}',
            '--chromedriver-downloads=1',
            f'--chrome-args={chrome_args}',  # should still work even with spaces
            f'--pdf-kwargs-json={pdf_kwargs_json_path}',
        ]
        # these alternate args are functionally equivalent to the above. make sure they work too.
        # - kwargs before args
        # - reverse order of kwargs
        # - uses "--key value" instead of "--key=value", both are valid under Python's argparse
        args_alternate = [
            PY_EXE,
            '-m',
            'chromepdf',
            'generate-pdf',
            '--pdf-kwargs-json', pdf_kwargs_json_path,
            '--chrome-args', f'{chrome_args}',
            '--chromedriver-downloads', '1',
            '--chromedriver-path', chromedriver_path,
            '--chrome-path', chrome_path,
            inpath,
            outpath,
        ]

        arg_list = [args_original, args_alternate]

        for args in arg_list:
            with self.subTest(args=args):

                proc = subprocess_run(args)   # pylint: disable=subprocess-run-check
                self.assertEqual(b'', proc.stdout)
                self.assertEqual(b'', proc.stderr)
                self.assertEqual(0, proc.returncode)

                self.assertTrue(os.path.exists(outpath))
                with open(outpath, 'rb') as f:
                    pdf_bytes = f.read()
                os.remove(outpath)

                self.assertEqual(1, extractText(pdf_bytes).count(html))

                # ensure all parameters got through
                with mock.patch('chromepdf.shortcuts.generate_pdf') as m:
                    m.return_value = b'12345'
                    chromepdf_run(args[3:])

                m.assert_called_with(
                    html,
                    pdf_kwargs,
                    chrome_path=chrome_path,
                    chromedriver_path=chromedriver_path,
                    chromedriver_downloads=True,
                    chrome_args=chrome_args_list,
                )
