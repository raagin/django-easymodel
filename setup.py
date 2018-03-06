#!/usr/bin/env python
import os
import re

from setuptools import setup, find_packages


description="""Easy Model translation for Django. 
Based on https://github.com/specialunderwear/django-easymode
"""

version = '0.0.1'
packages = []
data_files = []

setup(name='django-easymodel',
    version=version,
    description='Easy Model translation for Django',
    author='Yury Lapshinov',
    author_email='y.raagin@gmail.com',
    maintainer='Yury Lapshinov',
    maintainer_email='y.raagin@gmail.com',
    keywords='i18n internationalization translate django',
    long_description=description,
    install_requires=[
        'setuptools',
        'django>=1.11',
    ],
    url='http://github.com/raagin/django-easymodel',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    # for avoiding conflict have one namespace for all apc related eggs.
    namespace_packages=[],
    # include non python files
    include_package_data=True,
    zip_safe=False,
    platforms = "any",
    license='GPL',
    classifiers=[
        'Development Status :: Progress',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Software Development :: Localization',
    ],
)