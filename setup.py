from setuptools import setup, find_packages


setup(
    name='terracotta',
    version='0.1.0',
    description='An XYZ tile server written in Python',
    author='Philip Graae',
    author_email='phgr@dhigroup.com',
    packages=find_packages(),
    entry_points='''
        [console_scripts]
        terracotta=terracotta.cli:cli
    ''',
)
