import os
import re
import subprocess
import sys
from os.path import relpath


def system(*args, **kwargs):
    kwargs.setdefault('stdout', subprocess.PIPE)
    proc = subprocess.Popen(args, **kwargs)
    out, _err = proc.communicate()
    return out


def _find_nonascii(s):
    """
    Return a list of (line#, [col#, col#, col#]) tuples, one per line, that identify the positions of non-ascii characters.
    Lines without non-ascii characters are skipped.
    Returns an empty list if none found.
    Number values are zero-indexed.
    """

    outvals = []
    lines = s.split('\n')
    for il, l in enumerate(lines):
        colnums = []
        for ic, c in enumerate(l):
            if not (0 <= ord(c) <= 127):
                colnums.append(ic)
        if colnums:
            #print(len(l), l)
            #print(['%X' % ord(c) for c in l])
            #print(len(l.encode('utf8')), l.encode('utf8'))
            outvals.append((il, colnums))
    return outvals


def nonascii(filepath):
    """
    Raise exception if any code files contain non-ascii characters.
    Python 3 should be unicode by default. But as of Aug 2020 we see no reason to allow non-ascii characters.
    """

    filepath = relpath(filepath)  # relpath is more concise in output than absolute path

    # don't perform this check if it's not a code file
    suffix = filepath.split('.')[-1].lower()
    if suffix not in ('py', 'css', 'js', 'html'):
        return

    with open(filepath, 'r', encoding='utf8') as f:
        s = f.read()
        nonascii_locations = _find_nonascii(s)

        if nonascii_locations:
            s_lines = s.split('\n')
            # for each line with nonascii characters...
            for linenum, colnums in nonascii_locations:
                colnums_set = set(colnums)

                # create a text string that replaces offending chars with '[?]'
                s_fixed = ''.join('[?]' if i in colnums_set else s for i, s in enumerate(s_lines[linenum]))
                # output the first offender's position (1-indexed)
                print('%s: Line %d, Col %d: "%s"' % (filepath, linenum + 1, colnums[0] + 1, s_fixed))

            exit(1)  # aborts the commit


def autopep8(filepath):
    """Auto-format the code file at filepath."""

    # select or ignore, not both
    # list of codes can be found here: https://github.com/hhatto/autopep8#features
    select_codes = []
    ignore_codes = [
        'E501',  # c /2068/
        'E402', 'E401',  # these are import-related. isort takes care of those.
    ]
    overrides = ["--max-line-length=120", "--aggressive"]

    args = ['autopep8', '--in-place']
    if select_codes and ignore_codes:
        print('Error: select and ignore codes are mutually exclusive')
        exit(1)
    elif select_codes:
        args.extend(('--select', ','.join(select_codes)))
    elif ignore_codes:
        args.extend(('--ignore', ','.join(ignore_codes)))
    args.extend(overrides)
    args.append(filepath)
    _output = system(*args)


def run_pylint(files, outfile=None):
    """Run pylint on a list containing directories and/or file paths."""
    assert not isinstance(files, str)  # must be a list of stringss

    from pylint.lint.run import Run as PyLint_Run

    class WritableObject:
        "dummy output stream for pylint"

        def __init__(self):
            self.content = []

        def write(self, st):
            "dummy write"
            self.content.append(st)

        def read(self):
            "dummy read"
            return self.content
    from pylint.reporters.text import TextReporter
    pylint_output = WritableObject()

    project_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
    rcfilepath = os.path.join(project_base_dir, '.pylintrc')
    if not os.path.exists(rcfilepath):
        print('Pylint could not find rcfile: %s' % rcfilepath)
        exit(1)
    pylint_args = ['--rcfile', rcfilepath, *files]

    PyLint_Run(pylint_args, reporter=TextReporter(pylint_output), exit=False)
    has_errors = False

    if outfile is None:  # print output to stdout
        for l in pylint_output.read():
            if l.strip():  # skip empty lines
                print(l.rstrip())  # remove training newline so we only print one newline
                if l.strip().startswith('chromepdf') or l.strip().startswith('testapp'):
                    has_errors = True
    else:
        outfilepath = os.path.join(project_base_dir, outfile)
        print(outfilepath)
        #pylint_args.extend(['>',outfilepath, ''])
        with open(outfilepath, 'w') as f:
            for l in pylint_output.read():
                f.write(l)

    if has_errors:
        print('Pylint detected errors, aborting')
        exit(1)


def main():
    """
    Perform all pre-commit checks on files that are included in the commit.
    In order to abort the commit, call exit(1) from anywhere in this file.
    """

    # Abort if required libraries are not installed
    try:
        import autopep8 as _ap8  # @UnusedImport
        from isort.hooks import git_hook as isort_git_hook

        # from flake8.main.git import hook as flake8_git_hook # we are not using flake8
        # from pylint.lint.run import Run as _PyLint_Run  # @UnusedImport
    except ImportError:
        print("'autopep8' and 'isort' are required.", file=sys.stderr)
        exit(1)

    # Get list of files being committed.
    modified_pyfiles_re = re.compile(r'^[AM]+\s+(?P<name>.*\.py)$', re.MULTILINE)  # @UndefinedVariable
    basedir = system('git', 'rev-parse', '--show-toplevel').decode("utf-8").strip()
    all_files = system('git', 'status', '--porcelain').decode("utf-8")
    py_files = modified_pyfiles_re.findall(all_files)

    # check for nonascii characters in modified files.
    print('Running non-ascii character check...')
    for name in all_files:
        filepath = os.path.join(basedir, name)
        nonascii(filepath)

    # isort: sort import statements at top of file.
    print('Running isort to sort import statements...')
    isort_git_hook(strict=False, modify=True)

    # autopep8: run code auto-formatter on modified files
    print('Running autopep8 code formatter...')
    for name in py_files:
        filepath = os.path.join(basedir, name)
        nonascii(filepath)
        autopep8(filepath)
        system("git", "add", filepath)

#     # pylint will run code linter and abort if errors/warnings detected
#     print('Running pylint...')
#     files_joined = [os.path.join(basedir, f) for f in files if f.endswith('.py')]  # .py files only
#     if files_joined:
#         run_pylint(files_joined)

    # we are not using flake8.
#     # flake8: check for syntax errors/warnings
#     # lazy: will only check files in this commit, not all
#     # strict: will abort commit if issues found
#     flake8_git_hook(lazy=True, strict=True)


if __name__ == '__main__':
    main()
