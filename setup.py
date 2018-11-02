from setuptools import setup, find_packages


setup(
    name='terracotta',
    description='A modern XYZ tile server written in Python',
    author='Philip Graae',
    author_email='phgr@dhigroup.com',
    packages=find_packages(),
    python_requires='>=3.6',
    use_scm_version={
        'write_to': 'terracotta/_version.py'
    },
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
        'numpy',
        'pillow',
        'shapely',
        'rasterio>=1.0,<1.0.7',
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
            'codecov',
            'attrs>=17.4.0',
            'matplotlib',
            'moto',
            'crick'
        ],
        'docs': [
            'sphinx',
            'sphinx_autodoc_typehints'
        ],
        'recommended': [
            'colorlog',
            'crick',
        ]
    },
    entry_points='''
        [console_scripts]
        terracotta=terracotta.scripts.cli:entrypoint
    ''',
    include_package_data=True,
    package_data={
        'terracotta': [
            'cmaps/*_rgb.npy',  # colormaps
            'templates/*.html', 'static/*.js', 'static/*.css', 'static/images/*.png'  # preview app
        ]
    }
)
