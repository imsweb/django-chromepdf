import json
import os
import shutil
import subprocess
from unittest import mock
from unittest.case import TestCase

from django.conf import settings

from chromepdf.run import chromepdf_run
from chromepdf.webdrivers import _get_chromedriver_environment_path
from testapp.tests.utils import extractText, findChromePath


class CommandLineTests(TestCase):
    """Test generating PDFs via the command line."""

    @classmethod
    def setUpClass(cls):
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.TEMP_DIR)

    def test_run_no_args(self):
        """Should display help text"""

        proc = subprocess.run(['python', '-m', 'chromepdf'], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertIn('usage:', proc.stdout.decode('utf8'))  # dispalys help text?
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_error_no_args(self):
        """Should display an error about the subcommand 'generate-pdf'"""

        proc = subprocess.run(['python', '-m', 'chromepdf', 'generate-pdf'], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn('generate-pdf: requires one or two path arguments', proc.stderr.decode('utf8'))  # dispalys help text?
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_error_too_many_args(self):
        """Should display an error re: the number of arguments."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)

        proc = subprocess.run(['python', '-m', 'chromepdf', 'generate-pdf', inpath, inpath, inpath], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn('generate-pdf: requires one or two path arguments', proc.stderr.decode('utf8'))  # dispalys help text?
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_error_missing_input_file(self):
        """Should display an error re: the number of arguments."""

        inpath = os.path.join(settings.TEMP_DIR, 'file-not-found.html')

        proc = subprocess.run(['python', '-m', 'chromepdf', 'generate-pdf', inpath], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertIn('generate-pdf: could not find input html file: ', proc.stderr.decode('utf8'))  # dispalys help text?
        self.assertEqual(2, proc.returncode)

    def test_generate_pdf_inpath(self):
        """Generate a PDF where only the inpath is provided."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.rev1.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess.run(['python', '-m', 'chromepdf', 'generate-pdf', inpath], capture_output=True)   # pylint: disable=subprocess-run-check
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(0, proc.returncode)

        outpath = inpath.replace('.html', '.pdf')
        self.assertTrue(os.path.exists(outpath))
        with open(outpath, 'rb') as f:
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
        proc = subprocess.run(['python', '-m', 'chromepdf', 'generate-pdf', inpath], capture_output=True)   # pylint: disable=subprocess-run-check
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

    def test_generate_pdf_inpath_outpath(self):
        """Generate a PDF where the inpath AND outpath are provided."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        outpath = os.path.join(settings.TEMP_DIR, 'output.pdf')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess.run(['python', '-m', 'chromepdf', 'generate-pdf', inpath, outpath], capture_output=True)   # pylint: disable=subprocess-run-check
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
        chrome_args_list = ['--no-sandbox']
        chrome_args = ' '.join(chrome_args_list)
        pdf_kwargs = {'margin': 1, 'marginLeft': '1in'}
        pdf_kwargs_json_path = os.path.join(settings.TEMP_DIR, 'pdf_kwargs.json')
        with open(pdf_kwargs_json_path, 'w', encoding='utf8') as f:
            f.write(json.dumps(pdf_kwargs))

        args = [
            'python',
            '-m',
            'chromepdf',
            'generate-pdf',
            inpath,
            outpath,
            f'--chrome-path={chrome_path}',
            f'--chromedriver-path={chromedriver_path}',
            '--chromedriver-downloads=1',
            f'--chrome-args={chrome_args}',
            f'--pdf-kwargs-json={pdf_kwargs_json_path}',
        ]
        # print(args)
        proc = subprocess.run(args, capture_output=True)   # pylint: disable=subprocess-run-check
        # print(proc.stdout)
        # print(proc.stderr)
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)
        self.assertEqual(0, proc.returncode)

        self.assertTrue(os.path.exists(outpath))
        with open(outpath, 'rb') as f:
            pdf_bytes = f.read()

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
