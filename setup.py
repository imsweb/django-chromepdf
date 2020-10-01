from setuptools import find_packages, setup

setup(
    name='chromepdf',
    version='1.1.0',  # Make sure to update the string in chromepdf.__init__.__version__ too
    description='ChromePDF is a small Django application that uses Selenium and Google Chrome to convert HTML into a PDF.',
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
        'selenium~=3.141.0'
    ],
)
