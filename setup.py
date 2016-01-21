#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frequent used classifiers List = [
    "Development Status :: 1 - Planning",
    "Development Status :: 2 - Pre-Alpha",
    "Development Status :: 3 - Alpha",
    "Development Status :: 4 - Beta",
    "Development Status :: 5 - Production/Stable",
    "Development Status :: 6 - Mature",
    "Development Status :: 7 - Inactive",

    "Intended Audience :: Customer Service",
    "Intended Audience :: Developers",
    "Intended Audience :: Education",
    "Intended Audience :: End Users/Desktop",
    "Intended Audience :: Financial and Insurance Industry",
    "Intended Audience :: Healthcare Industry",
    "Intended Audience :: Information Technology",
    "Intended Audience :: Legal Industry",
    "Intended Audience :: Manufacturing",
    "Intended Audience :: Other Audience",
    "Intended Audience :: Religion",
    "Intended Audience :: Science/Research",
    "Intended Audience :: System Administrators",
    "Intended Audience :: Telecommunications Industry",

    "License :: OSI Approved :: BSD License",
    "License :: OSI Approved :: MIT License",
    "License :: OSI Approved :: Apache Software License",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",

    "Natural Language :: English",
    "Natural Language :: Chinese (Simplified)",

    "Operating System :: Microsoft :: Windows",
    "Operating System :: MacOS",
    "Operating System :: Unix",
    
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 2 :: Only",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3 :: Only",
]
"""

from setuptools import setup, find_packages
from datetime import datetime
import os

GITHUB_ACCOUNT = "MacHu-GWU" # your GitHub account name
RELEASE_TAG = "2016-01-20" # the GitHub release tag
NAME = "uszipcode" # name your package

VERSION = __import__(NAME).__version__
PACKAGES = [NAME] + ["%s.%s" % (NAME, i) for i in find_packages(NAME)]
PACKAGE_DATA = {
    "uszipcode": ["data/zipcode.sqlite3"],
}
SHORT_DESCRIPTION = __import__(NAME).__short_description__ # GitHub Short Description
AUTHOR = "Sanhe Hu"
AUTHOR_EMAIL = "husanhe@gmail.com"
MAINTAINER = AUTHOR
MAINTAINER_EMAIL = AUTHOR_EMAIL

PROJECT_NAME = os.path.basename(os.getcwd()) # the project dir is the project name
URL = "https://github.com/{0}/{1}".format(GITHUB_ACCOUNT, PROJECT_NAME)
DOWNLOAD_URL = "https://github.com/{0}/{1}/tarball/{2}".format(
    GITHUB_ACCOUNT, PROJECT_NAME, RELEASE_TAG)

with open("long_description.rst", "rb") as f:
    LONG_DESCRIPTION = f.read().decode("utf-8")
LICENSE = "MIT"

PLATFORMS = ["Windows", "MacOS", "Unix"]
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: MacOS",
    "Operating System :: Unix",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
]

with open("requirements.txt", "rb") as f:
    REQUIRES = [i.strip() for i in f.read().decode("utf-8").split("\n")]
    
setup(
    name = NAME,
    packages = PACKAGES,
    include_package_data = True,
    package_data  = PACKAGE_DATA,
    version = VERSION,
    author = AUTHOR,
    author_email = AUTHOR_EMAIL,
    maintainer = MAINTAINER,
    maintainer_email = MAINTAINER_EMAIL,
    url = URL,
    description = SHORT_DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    download_url = DOWNLOAD_URL,
    classifiers = CLASSIFIERS,
    platforms = PLATFORMS,
    license = LICENSE,
    install_requires = REQUIRES,
)