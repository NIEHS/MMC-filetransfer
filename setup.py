#! /usr/env/bin python
from setuptools import setup

setup(
    name='MMC',
    version='0.2',
    description='Filetransfer/auto-process initiating script',
    author='Jonathan Bouvette',
    author_email='jonathan.bouvette@nih.gov',
    packages=['MMC'],  # same as name
    install_requires=['pydantic', 'python-dotenv', 'pyyaml'],  # external packages as dependencies
    scripts=[
        'MMC/bin/mmc.py',
    ],
)
