import os
import re

from setuptools import find_packages, setup


def get_version():
    with open(os.path.join(os.path.dirname(__file__), 'chromepdf', '__init__.py')) as fp:
        return re.match(r".*__version__ = '(.*?)'", fp.read(), re.S).group(1)  # @UndefinedVariable


def get_long_description():
    with open(os.path.join(os.path.dirname(__file__), 'README.md')) as fp:
        return fp.read()


setup(
    name='django-chromepdf',
    version=get_version(),  # Make sure to update the string in chromepdf.__init__.__version__ too
    description='ChromePDF is a small Python 3 library that uses Selenium and Google Chrome to convert HTML into a PDF.',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Andrew Kukwa',
    author_email='kukwaa@imsweb.com',
    url='https://github.com/imsweb/django-chromepdf',
    license='BSD',
    packages=find_packages(exclude=('testapp',)),
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
    install_requires=[
        'selenium<5,>=3'
    ],
)
