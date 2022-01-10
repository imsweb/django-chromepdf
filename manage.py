#!/usr/bin/env python
import os
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

    # do some checks so environment tests will pass.
    # TODO: Create a TestRunner subclass for this later.
    if 'test' in sys.argv:
        import shutil
        from chromepdf.webdrivers import get_chrome_version
        from testapp.tests.utils import findChromePath

        chromedriver_path = shutil.which('chromedriver.exe')
        chrome_path = findChromePath()
        if chrome_path is None:
            raise EnvironmentError('You must have a chrome.exe on your PATH.')
        if chromedriver_path is None:
            raise EnvironmentError('You must have a chromedriver.exe on your PATH.')

        chrome_version = get_chrome_version(chrome_path)
        chromedriver_version = subprocess.Popen(['chromedriver.exe', '--version'], stdout=subprocess.PIPE).communicate()[0].decode('utf8')
        # Output is, EG: b'ChromeDriver 95.0.4638.54 (d31a821ec901f68d0d34ccdbaea45b4c86ce543e-refs/branch-heads/4638@{#871})\r\n
        chromedriver_version = chromedriver_version.split()[1]  # 95.0.4638.54
        chromedriver_version = [int(c) for c in chromedriver_version.split('.')]  # (95,0,4638,54)
        if chrome_version[0] != chromedriver_version[0]:
            raise EnvironmentError(f'Your PATH chromedriver version does not match your default chrome version: Chrome={chrome_version[0]}, Chromedriver={chromedriver_version[0]} (located at "{chromedriver_path}"). Make sure these match before running your tests.')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
