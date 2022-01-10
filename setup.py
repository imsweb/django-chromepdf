import os
import re

from setuptools import find_packages, setup

_GITHUB_MASTER_ROOT = 'https://github.com/imsweb/django-chromepdf/blob/master/'


def get_version():
    """Return the version string stored at chromepdf.__version__"""
    with open(os.path.join(os.path.dirname(__file__), 'chromepdf', '__init__.py')) as fp:
        return re.match(r".*__version__ = '(.*?)'", fp.read(), re.S).group(1)  # @UndefinedVariable


def get_long_description():
    """
    Return a long description consisting of the readme's contents.
    The contents are Markdown, so be sure to set the "long_description_content_type" accordingly.
    """
    with open(os.path.join(os.path.dirname(__file__), 'README.md')) as fp:
        contents = fp.read()
        # expand relative girhub urls to absolute. this will match EVERY url in the document.
        contents = re.sub(r'\[(.+?)\]\((.+?)\)', r'[\1](%s\2)' % _GITHUB_MASTER_ROOT, contents)
        # un-expand urls that were already absolute.
        contents = contents.replace(f'{_GITHUB_MASTER_ROOT}https://', 'https://')
        return contents


setup(
    name='django-chromepdf',
    version=get_version(),  # Make sure to update the string in chromepdf.__init__.__version__ too
    description='A small Python 3 library that uses Selenium and Google Chrome to convert HTML into a PDF.',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Andrew Kukwa',
    author_email='kukwaa@imsweb.com',
    url='https://github.com/imsweb/django-chromepdf',
    license='BSD',
    packages=find_packages(exclude=('testapp',)),
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
    ],
    python_requires='~=3.6',
    install_requires=[
        'selenium<5,>=3'
    ],
)
