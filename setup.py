from setuptools import setup, find_packages
from os import path
import re

here = path.abspath(path.dirname(__file__))

# get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# resolve relative links to figures
long_description = re.sub(
    r'!\[(\w+)\]\((docs/_figures/.*)\)',
    r'![\1](https://github.com/DHI-GRAS/terracotta/tree/master/\2?raw=true)',
    long_description
)

setup(
    # metadata
    name='terracotta',
    description='A modern XYZ tile server written in Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/DHI-GRAS/terracotta',
    author='Philip Graae',
    author_email='phgr@dhigroup.com',
    keywords='xyz tileserver rasterio cloud-optimized-geotiff serverless',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Flask',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Unix',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Scientific/Engineering :: GIS'
    ],
    # module
    packages=find_packages(exclude=['docs', 'tests']),
    python_requires='>=3.6',
    use_scm_version={
        'write_to': 'terracotta/_version.py'
    },
    # dependencies
    setup_requires=[
        'setuptools_scm',
        'setuptools_scm_git_archive',
        'numpy'
    ],
    install_requires=[
        'apispec',
        'cachetools',
        'click',
        'flask',
        'flask_cors',
        'marshmallow>=3.0.0b12',
        'mercantile',
        'numpy>=1.15',
        'pillow',
        'shapely',
        'rasterio>=1.0',
        'shapely',
        'toml',
        'tqdm'
    ],
    extras_require={
        'test': [
            'pytest>=3.5',
            'pytest-cov',
            'pytest-mypy',
            'pytest-flake8',
            'pytest-benchmark',
            'attrs>=17.4.0',
            'codecov',
            'colorlog',
            'crick',
            'matplotlib',
            'moto',
            'pymysql'
        ],
        'docs': [
            'sphinx',
            'sphinx_autodoc_typehints',
            'sphinx-click',
            'pymysql'
        ],
        'recommended': [
            'colorlog',
            'crick',
            'pymysql'
        ]
    },
    # CLI
    entry_points='''
        [console_scripts]
        terracotta=terracotta.scripts.cli:entrypoint
    ''',
    # package data
    include_package_data=True,
    package_data={
        'terracotta': [
            'cmaps/*_rgb.npy',  # colormaps
            'templates/*.html', 'static/*.js', 'static/*.css', 'static/images/*.png'  # preview app
        ]
    },
)
