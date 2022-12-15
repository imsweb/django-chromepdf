import os
import re

import setuptools
from setuptools import find_packages, setup


# setuptools 61.0.0 is the first to support pyproject.toml config file.
# See: https://setuptools.pypa.io/en/latest/history.html#v61-0-0
_PYPROJECT_TOML_SUPPORTED = int(setuptools.__version__.split('.')[0]) >= 61

if _PYPROJECT_TOML_SUPPORTED:
    # rely entirely on pyproject.toml if supported, and ignore this file's contents.
    setup_params = {}

else:
    # deprecated behavior: rely on old setup.py for Python 3.6 and any installs that have
    # setuptools < 61 installed.
    # setuptools 61 does not support Python 3.6, but we still do, because we still support
    # Selenium 3. So we must provide this workaround.
    # Support for Python 3.6 and Selenium 3 will end with the release of ChromePDF 2.0.

    _GITHUB_MASTER_ROOT = 'https://github.com/imsweb/django-chromepdf/blob/master/'

    def get_version():
        """Return the version string stored at chromepdf.__version__"""
        with open(os.path.join(os.path.dirname(__file__), 'chromepdf', '__init__.py'), encoding='utf8') as fp:
            return re.match(r".*__version__ = '(.*?)'", fp.read(), re.S).group(1)  # @UndefinedVariable

    def get_long_description():
        """
        Return a long description consisting of the readme's contents.
        The contents are Markdown, so be sure to set the "long_description_content_type" accordingly.
        Convert all relative urls into absolute ones so that they will display correctly on Pypi.
        """
        with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf8') as fp:
            contents = fp.read()
            # expand relative github urls to absolute. this will match EVERY url in the document.
            contents = re.sub(r'\[(.+?)\]\((.+?)\)', r'[\1](%s\2)' % _GITHUB_MASTER_ROOT, contents)
            # un-expand urls that were already absolute.
            contents = contents.replace(f'{_GITHUB_MASTER_ROOT}https://', 'https://')
            return contents

    def find_chromepdf_packages():
        return find_packages(exclude=['testapp', '*testapp*', 'testapp.*'])

    setup_params = dict(
        name='django-chromepdf',
        version=get_version(),
        description='A small Python 3 library that uses Selenium and Google Chrome to convert HTML into a PDF.',
        long_description=get_long_description(),
        long_description_content_type='text/markdown',
        author='Andrew Kukwa',
        author_email='kukwaa@imsweb.com',
        url='https://github.com/imsweb/django-chromepdf',
        license='BSD',
        packages=find_chromepdf_packages(),
        include_package_data=True,
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: POSIX',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: OS Independent',
            'Topic :: Utilities',
            'Topic :: Software Development :: Libraries',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
        ],
        python_requires='~=3.6',
        install_requires=[
            'selenium<5,>=3'
        ],
        project_urls={
            "Source": "https://github.com/imsweb/django-chromepdf",
            "Changelog": "https://github.com/imsweb/django-chromepdf/blob/master/CHANGELOG.md",
        },
    )

if __name__ == '__main__':
    # place setup() in conditional and keep params in global dict so unit tests can access them without calling setup()
    setup(**setup_params)
