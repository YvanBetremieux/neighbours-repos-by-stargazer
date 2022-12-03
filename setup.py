# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open("README.rst") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="stargazer",
    version="0.1.0",
    description="APi to retrieve linked project by stargazer",
    long_description=readme,
    author="Yvan Betremieux",
    author_email="yvan.betremieux@gmail.com",
    url="",
    license=license,
    packages=find_packages(exclude=("tests", "docs")),
)
