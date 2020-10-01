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

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
