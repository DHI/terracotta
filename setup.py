import versioneer

from setuptools import setup, find_packages


setup(
    name='terracotta',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='An XYZ tile server written in Python',
    author='Philip Graae',
    author_email='phgr@dhigroup.com',
    packages=find_packages(),
    python_requires='>=3.5',
    setup_requires=['numpy'],
    install_requires=[
        'numpy',
        'flask',
        'click',
        'pillow',
        'matplotlib',
        'mercantile',
        'rasterio>=1.0b1',
        'cachetools',
        'tqdm'
    ],
    entry_points='''
        [console_scripts]
        terracotta=terracotta.scripts.cli:cli
    ''',
    extras_require={
        'test': ['pytest', 'pytest-cov', 'pytest-mypy', 'pytest-flake8', 'codecov']
    },
    include_package_data=True,
    package_data={
        'terracotta': ['templates/*.html', 'static/*.js',
                       'static/*.css', 'static/images/*.png']
    }
)
