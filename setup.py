#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup script for the Huefy Python SDK."""

import os
import re
from setuptools import setup, find_packages

# Get the long description from the README file
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get version from __init__.py
with open(os.path.join(os.path.dirname(__file__), 'teracrafts_huefy', '__init__.py'), encoding='utf-8') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]$", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

setup(
    name='teracrafts-huefy',
    version=version,
    description='Official Python SDK for the Huefy email sending platform',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Huefy Team',
    author_email='developers@huefy.com',
    url='https://github.com/teracrafts/huefy-sdk',
    project_urls={
        'Documentation': 'https://docs.huefy.com/sdk/python',
        'Source': 'https://github.com/teracrafts/huefy-sdk',
        'Tracker': 'https://github.com/teracrafts/huefy-sdk/issues',
    },
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Email',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    keywords='huefy email api sdk template transactional',
    packages=find_packages(exclude=['tests*', 'examples*']),
    package_data={
        'teracrafts_huefy': ['py.typed'],
    },
    python_requires='>=3.8',
    install_requires=[
        'requests>=2.28.0,<3.0.0',
        'typing-extensions>=4.0.0,<5.0.0; python_version<"3.10"',
        'pydantic>=2.0.0,<3.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-asyncio>=0.21.0',
            'pytest-mock>=3.11.0',
            'responses>=0.23.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.4.0',
            'isort>=5.12.0',
            'pre-commit>=3.3.0',
        ],
        'async': [
            'httpx>=0.24.0,<1.0.0',
            'aiohttp>=3.8.0,<4.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'huefy=teracrafts_huefy.cli:main',
        ],
    },
    zip_safe=False,
)