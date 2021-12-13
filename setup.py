#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# read version string
with open(path.join(here, "siti_tools", "__init__.py")) as version_file:
    version = eval(version_file.read().split("\n")[0].split("=")[1].strip())

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Get the history from the CHANGELOG file
with open(path.join(here, "CHANGELOG.md"), encoding="utf-8") as f:
    history = f.read()

setup(
    name="siti-tools",
    version=version,
    description="Functions to calculate Spatial Information / Temporal Information according to ITU-T P.910",
    long_description=long_description + "\n\n" + history,
    long_description_content_type="text/markdown",
    author="Werner Robitza",
    author_email="werner.robitza@gmail.com",
    url="https://github.com/Telecommunication-Telemedia-Assessment/siti-tools",
    packages=["siti_tools"],
    include_package_data=True,
    install_requires=["scipy", "numpy", "av", "tqdm", "plotille"],
    license="MIT",
    zip_safe=False,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    keywords="video, spatial information, temporal information",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={"console_scripts": ["siti-tools = siti.__main__:main"]},
)
