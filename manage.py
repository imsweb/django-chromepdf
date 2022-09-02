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

    # easy way to download a chromedriver into current working dir, needed for unit tests.
    if 'getchromedriver' in sys.argv:
        from testapp.tests.utils import findChromePath
        chrome_path = findChromePath()
        if chrome_path is None:
            raise EnvironmentError('You must have a chrome.exe on your PATH.')
        from chromepdf.webdrivers import (download_chromedriver_version,
                                          get_chrome_version)
        version = get_chrome_version(chrome_path)
        path = download_chromedriver_version(version)
        if os.path.exists('chromedriver.exe'):
            os.remove('chromedriver.exe')
        os.rename(path, 'chromedriver.exe')
        exit(0)

    # do some checks so environment tests will pass.
    # TODO: Create a TestRunner subclass for this later.
    if 'test' in sys.argv:
        import shutil

        from chromepdf.webdrivers import get_chrome_version
        from testapp.tests.utils import findChromePath

        is_windows = (platform.system() == 'Windows')
        exe_filename = 'chromedriver.exe' if is_windows else 'chromedriver'

        chromedriver_path = shutil.which(exe_filename)
        chrome_path = findChromePath()
        if chrome_path is None:
            raise EnvironmentError('You must have a chrome.exe on your PATH.')
        if chromedriver_path is None:
            raise EnvironmentError(f"You must have a '{exe_filename}' on your PATH. Run manage.py getchromedriver to fetch one.")

        chrome_version = get_chrome_version(chrome_path)
        chromedriver_version = subprocess.Popen([exe_filename, '--version'], stdout=subprocess.PIPE).communicate()[0].decode('utf8')
        # Output is, EG: b'ChromeDriver 95.0.4638.54 (d31a821ec901f68d0d34ccdbaea45b4c86ce543e-refs/branch-heads/4638@{#871})\r\n
        chromedriver_version = chromedriver_version.split()[1]  # 95.0.4638.54
        chromedriver_version = [int(c) for c in chromedriver_version.split('.')]  # (95,0,4638,54)
        if chrome_version[0] != chromedriver_version[0]:
            raise EnvironmentError(f'Your PATH chromedriver version does not match your default chrome version: Chrome={chrome_version[0]}, Chromedriver={chromedriver_version[0]} (located at "{chromedriver_path}"). Make sure these match before running your tests.')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")

    if 'entrypoint' in sys.argv:
        print('Running entry point...')
        from chromepdf.run import chromepdf_run
        command_line_interface(sys.argv[2:])
        exit()

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
