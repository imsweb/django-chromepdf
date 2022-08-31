import os
import shutil
import subprocess
from unittest import mock
from unittest.case import TestCase

from django.conf import settings

from chromepdf.run import command_line_interface
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

        proc = subprocess.run(['python', '-m', 'chromepdf.run'], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertEqual(2, proc.returncode)
        self.assertIn('usage:', proc.stdout.decode('utf8'))  # dispalys help text?
        self.assertEqual(b'', proc.stderr)

    def test_generate_pdf_error_no_args(self):

        proc = subprocess.run(['python', '-m', 'chromepdf.run', '--generate-pdf'], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertEqual(2, proc.returncode)
        self.assertEqual(b'', proc.stdout)
        self.assertIn('--generate-pdf: requires one or two path arguments', proc.stderr.decode('utf8'))  # dispalys help text?

    def test_generate_pdf_error_too_many_args(self):

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)

        proc = subprocess.run(['python', '-m', 'chromepdf.run', '--generate-pdf', inpath, inpath, inpath], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertEqual(2, proc.returncode)
        self.assertEqual(b'', proc.stdout)
        self.assertIn('--generate-pdf: requires one or two path arguments', proc.stderr.decode('utf8'))  # dispalys help text?

    def test_generate_pdf_error_missing_input_file(self):

        inpath = os.path.join(settings.TEMP_DIR, 'file-not-found.html')

        proc = subprocess.run(['python', '-m', 'chromepdf.run', '--generate-pdf', inpath], capture_output=True)  # pylint: disable=subprocess-run-check
        self.assertEqual(2, proc.returncode)
        self.assertEqual(b'', proc.stdout)
        self.assertIn('--generate-pdf: could not find input html file: ', proc.stderr.decode('utf8'))  # dispalys help text?

    def test_generate_pdf_inpath(self):
        "Generate a PDF where only the inpath is provided."

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.rev1.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess.run(['python', '-m', 'chromepdf.run', '--generate-pdf', inpath], capture_output=True)   # pylint: disable=subprocess-run-check
        self.assertEqual(0, proc.returncode)
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)

        outpath = inpath.replace('.html', '.pdf')
        self.assertTrue(os.path.exists(outpath))
        with open(outpath, 'rb') as f:
            pdf_bytes = f.read()

        self.assertEqual(1, extractText(pdf_bytes).count(html))

    def test_generate_pdf_inpath_outpath(self):
        "Generate a PDF where the inpath AND outpath are provided."

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        outpath = os.path.join(settings.TEMP_DIR, 'output.pdf')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        proc = subprocess.run(['python', '-m', 'chromepdf.run', '--generate-pdf', inpath, outpath], capture_output=True)   # pylint: disable=subprocess-run-check
        self.assertEqual(0, proc.returncode)
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)

        self.assertTrue(os.path.exists(outpath))
        with open(outpath, 'rb') as f:
            pdf_bytes = f.read()

        self.assertEqual(1, extractText(pdf_bytes).count(html))

    def test_generate_pdf_all_kwargs(self):
        """Pass all kwargs through run interface."""

        html = 'One Word'
        inpath = os.path.join(settings.TEMP_DIR, 'input.html')
        with open(inpath, 'w', encoding='utf8') as f:
            f.write(html)
        outpath = inpath.replace('.html', '.pdf')

        chrome_path = findChromePath()
        chromedriver_path = _get_chromedriver_environment_path()
        chrome_args_list = ['--no-sandbox']
        chrome_args = ' '.join(chrome_args_list)
        # pdf_kwargs_dict = {'margin': 1, 'marginLeft':'1in'}
        # pdf_kwargs = json.dumps(pdf_kwargs_dict).replace('"','\\"')

        args = [
            'python',
            '-m',
            'chromepdf.run',
            '--generate-pdf',
            inpath,
            outpath,
            f'--chrome-path={chrome_path}',
            f'--chromedriver-path={chromedriver_path}',
            '--chromedriver-downloads=1',
            f'--chrome-args={chrome_args}',
            # f'--pdf-kwargs="{pdf_kwargs}"',
        ]
        # print(args)
        proc = subprocess.run(args, capture_output=True)   # pylint: disable=subprocess-run-check
        # print(proc.stdout)
        # print(proc.stderr)
        self.assertEqual(0, proc.returncode)
        self.assertEqual(b'', proc.stdout)
        self.assertEqual(b'', proc.stderr)

        self.assertTrue(os.path.exists(outpath))
        with open(outpath, 'rb') as f:
            pdf_bytes = f.read()

        self.assertEqual(1, extractText(pdf_bytes).count(html))

        # ensure all parameters got through

        with mock.patch('chromepdf.shortcuts.generate_pdf') as m:
            m.return_value = b'12345'
            command_line_interface(args[3:])

        m.assert_called_with(
            html,
            None,
            chrome_path=chrome_path,
            chromedriver_path=chromedriver_path,
            chromedriver_downloads=True,
            chrome_args=chrome_args_list,
        )
