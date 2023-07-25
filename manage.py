#!/usr/bin/env python
import os
import platform
import subprocess
import sys


if __name__ == "__main__":

    # enforce project-specific git hooks
    # manage.py is typically run at least once before committing.
    # so this ensures we set hooks without any manual input.
    cwd = os.path.abspath(os.path.dirname(__file__))
    githooks_path = os.path.join(cwd, 'testapp', 'githooks')
    # print(githooks_path)
    subprocess.call(['git', 'config', 'core.hooksPath', githooks_path], cwd=cwd)

    is_windows = (platform.system() == 'Windows')
    chromedriver_filename = 'chromedriver.exe' if is_windows else 'chromedriver'

    # Test generating a PDF without selenium
    if 'testnoselenium' in sys.argv:
        import pathlib
        myhtml = 'SPACE'

        # outbytes = generate_pdf_old(html=myhtml, pdf_kwargs=pdf_kwargs)
        path = pathlib.Path(__file__).parent
        chromedriver_path = path / 'chromedriver.exe'
        from testapp.tests.utils import findChromePath
        chrome_path = findChromePath()

        from chromepdf.shortcuts import generate_pdf

        outbytes = generate_pdf(html=myhtml, chrome_path=chrome_path, chromedriver_path=chromedriver_path, use_selenium=False)

        #outbytes = generate_pdf(url='https://www.google.com', pdf_kwargs=params)
        with open('file.pdf', 'wb') as f:
            f.write(outbytes)
        exit(0)

    # easy way to download a chromedriver into current working dir, needed for unit tests.
    if 'getchromedriver' in sys.argv:
        from testapp.tests.utils import findChromePath
        chrome_path = findChromePath()
        if chrome_path is None:
            raise EnvironmentError('You must have a chrome.exe on your PATH.')
        from chromepdf.webdrivers import download_chromedriver_version, get_chrome_version
        version = get_chrome_version(chrome_path, as_tuple=False)
        print(f'Downloading chromedriver version {version}')
        path = download_chromedriver_version(version)
        if os.path.exists(chromedriver_filename):
            os.remove(chromedriver_filename)
        os.rename(path, chromedriver_filename)
        exit(0)

    # do some checks so environment tests will pass.
    # TODO: Create a TestRunner subclass for this later.
    if 'test' in sys.argv:
        import shutil

        from chromepdf.webdrivers import find_chrome, get_chrome_version

        chromedriver_path = shutil.which(chromedriver_filename)
        chrome_path = find_chrome()  # chrome must be on PATH for no-selenium tests.
        if chrome_path is None:
            raise EnvironmentError('You must have a chrome/chrome.exe on your PATH.')
        if chromedriver_path is None:
            raise EnvironmentError(f"You must have a '{chromedriver_filename}' on your PATH. Run manage.py getchromedriver to fetch one.")

        chrome_version = get_chrome_version(chrome_path, as_tuple=False)
        with subprocess.Popen([chromedriver_filename, '--version'], stdout=subprocess.PIPE) as p:
            chromedriver_version = p.communicate()[0].decode('utf8')
        # Output is, EG: b'ChromeDriver 95.0.4638.54 (d31a821ec901f68d0d34ccdbaea45b4c86ce543e-refs/branch-heads/4638@{#871})\r\n
        chromedriver_version = chromedriver_version.split()[1]  # 95.0.4638.54
        if chrome_version.split('.')[0] != chromedriver_version.split('.')[0]:
            raise EnvironmentError(f'Your PATH chromedriver version does not match your default chrome version: Chrome={chrome_version}, Chromedriver={chromedriver_version} (located at "{chromedriver_path}"). Make sure these match before running your tests. Run "manage.py getchromedriver" to fetch one.')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
