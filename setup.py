"""
Setup file for locks.
"""

import io
import os
import re

from setuptools import setup


def get_metadata():
    """
    Return metadata for locks.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    init_path = os.path.join(here, 'locks.py')
    readme_path = os.path.join(here, 'README.md')

    with io.open(init_path, encoding='utf-8') as f:
        about_text = f.read()

    metadata = {
        key: re.search(r'__' + key + r"__ = '(.*?)'", about_text).group(1)
        for key in (
            'title',
            'version',
            'url',
            'author',
            'author_email',
            'license',
            'description',
        )
    }
    metadata['name'] = metadata.pop('title')

    with io.open(readme_path, encoding='utf-8') as f:
        metadata['long_description'] = f.read()
        metadata['long_description_content_type'] = 'text/markdown'

    return metadata


metadata = get_metadata()

# Primary requirements
install_requires = ['monotonic >=1.0']

setup(
    # Options
    install_requires=install_requires,
    python_requires='>=3.5',
    py_modules=['locks'],
    # Metadata
    download_url='{url}/archive/{version}.tar.gz'.format(**metadata),
    project_urls={'Issue Tracker': '{url}/issues'.format(**metadata)},
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    **metadata
)
