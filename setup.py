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
    install_requires=['numpy',
                      'flask',
                      'click',
                      'pillow',
                      'frozendict',
                      'matplotlib',
                      'mercantile',
                      'rasterio',
                      'cachetools'
                      ],
    entry_points='''
        [console_scripts]
        terracotta=terracotta.cli:cli
    ''',
)
