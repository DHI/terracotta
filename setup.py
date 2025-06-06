from setuptools import setup, find_packages
from os import path
import re

here = path.abspath(path.dirname(__file__))

# get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# resolve relative links to figures
long_description = re.sub(
    r"!\[(.*?)\]\((docs/_figures/.*?)\)",
    r"![\1](https://github.com/DHI/terracotta/raw/main/\2)",
    long_description,
)

numpy_constraints = (
    ">=1.15",
    "!=1.17.0",
)
numpy_version = ",".join(numpy_constraints)

setup(
    # metadata
    name="terracotta",
    description="A modern XYZ tile server written in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DHI/terracotta",
    author="Dion Häfner",
    author_email="mail@dionhaefner.de",
    keywords="xyz tileserver rasterio cloud-optimized-geotiff serverless",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: Flask",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Unix",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Multimedia :: Graphics :: Viewers",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    # module
    packages=find_packages(exclude=["docs", "tests"]),
    python_requires=">=3.9",
    use_scm_version={"write_to": "terracotta/_version.py"},
    # dependencies
    setup_requires=[
        "setuptools_scm",
        "setuptools_scm_git_archive",
        "numpy%s" % numpy_version,
    ],
    install_requires=[
        "apispec>=1.0",
        "apispec-webframeworks",
        "cachetools>=3.1.0",
        "click",
        "click-spinner",
        "color-operations",
        "flask",
        "flask_cors",
        "marshmallow>=3.0.0",
        "mercantile",
        "numpy%s" % numpy_version,
        "pillow",
        "pyyaml>=3.10",  # downstream dependency of apispec
        "shapely",
        "rasterio>=1.3.0",
        "shapely",
        "sqlalchemy>=1.4.1",
        "toml",
        "tqdm",
    ],
    extras_require={
        ':python_version == "3.9"': ["numpy<2.0.0"],
        "test": [
            "pytest",
            "pytest-cov",
            "pytest-benchmark",
            "attrs>=17.4.0",
            "codecov",
            "colorlog",
            "crick",
            "matplotlib",
            "moto",
            "aws-xray-sdk",
            "pymysql>=1.0.0",
            "psycopg2",
        ],
        "docs": [
            "sphinx",
            "sphinx_autodoc_typehints",
            "sphinx-click",
            "pymysql>=1.0.0",
            "psycopg2",
        ],
        "recommended": ["colorlog", "crick", "pymysql>=1.0.0", "psycopg2"],
    },
    # CLI
    entry_points="""
        [console_scripts]
        terracotta=terracotta.scripts.cli:entrypoint
    """,
    # package data
    include_package_data=True,
    package_data={
        "terracotta": [
            "cmaps/data/*_rgba.npy",  # colormaps
            "templates/*.html",
            "static/*",  # preview app
        ]
    },
)
