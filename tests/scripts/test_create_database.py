import pytest
from click.testing import CliRunner

import os
import shutil

TEST_CASES = (
    {  # basic
        'filenames': ['foo.tif'],
        'input_pattern': '{name}.tif',
        'expected_keys': ['name'],
        'expected_datasets': [('foo',)]
    },
    {  # two keys
        'filenames': ['S2_20180101_B04.tif'],
        'input_pattern': '{sensor}_{date}_B04.tif',
        'expected_keys': ['sensor', 'date'],
        'expected_datasets': [('S2', '20180101')]
    },
    {  # subfolder
        'filenames': ['S2/20180101_B04.tif'],
        'input_pattern': '{sensor}/{date}_B04.tif',
        'expected_keys': ['sensor', 'date'],
        'expected_datasets': [('S2', '20180101')]
    },
    {  # wildcard magic
        'filenames': ['S2/20180101_B04.tif', 'S2/20180101_B05_median.tif'],
        'input_pattern': '{sensor}/{date}_{band}{}.tif',
        'expected_keys': ['sensor', 'date', 'band'],
        'expected_datasets': [('S2', '20180101', 'B04'), ('S2', '20180101', 'B05')]
    },
    {  # keys occuring more than once
        'filenames': ['S2/20180101/S2_20180101_B04.tif'],
        'input_pattern': '{sensor}/{date}/{sensor}_{date}_{band}.tif',
        'expected_keys': ['sensor', 'date', 'band'],
        'expected_datasets': [('S2', '20180101', 'B04')]
    },
    {  # {} in filename
        'filenames': ['bar.tif', '{foo}.tif'],
        'input_pattern': '{{{name}}}.tif',
        'expected_keys': ['name'],
        'expected_datasets': [('foo',)]
    },
    {  # unicode
        'filenames': ['$*)-?:_«}ä»/foo.tif'],
        'input_pattern': '{}/{name}.tif',
        'expected_keys': ['name'],
        'expected_datasets': [('foo',)]
    }
)

INVALID_TEST_CASES = (
    {
        'filenames': [],
        'input_pattern': 'notafile{key}.tif',
        'error_contains': 'matches no files'
    },
    {
        'filenames': ['dir1/foo.tif', 'dir2/foo.tif'],
        'input_pattern': '{}/{name}.tif',
        'error_contains': 'duplicate keys'
    },
    {
        'filenames': ['S2_B04.tif', 'S2_20180101_B04.tif'],
        'input_pattern': '{sensor}_{}.tif',
        'error_contains': 'duplicate keys'
    },
    {
        'filenames': [],
        'input_pattern': 'notafile.tif',
        'error_contains': 'at least one placeholder'
    },
    {
        'filenames': [],
        'input_pattern': 'notafile{.tif',
        'error_contains': 'invalid pattern'
    }
)


@pytest.fixture()
def tmpworkdir(tmpdir):
    orig_dir = os.getcwd()
    try:
        os.chdir(tmpdir)
        yield tmpdir
    finally:
        os.chdir(orig_dir)


def test_create_database(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{name}.tif'))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['create-database', input_pattern, '-o', str(outfile)])
    assert result.exit_code == 0
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == ('name',)
    assert driver.get_datasets() == {('img',): str(raster_file)}


@pytest.mark.parametrize('case', TEST_CASES)
@pytest.mark.parametrize('abspath', [True, False])
def test_create_database_pattern(case, abspath, raster_file, tmpworkdir):
    from terracotta.scripts import cli

    for infile in case['filenames']:
        temp_infile = tmpworkdir / infile
        os.makedirs(temp_infile.dirpath(), exist_ok=True)
        shutil.copy(raster_file, temp_infile)

    outfile = tmpworkdir / 'out.sqlite'

    if abspath:
        input_pattern = os.path.abspath(tmpworkdir / case['input_pattern'])
    else:
        input_pattern = case['input_pattern']

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['create-database', input_pattern, '-o', str(outfile)])
    assert result.exit_code == 0, result.output
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == tuple(case['expected_keys'])
    assert tuple(driver.get_datasets().keys()) == tuple(case['expected_datasets'])


@pytest.mark.parametrize('case', INVALID_TEST_CASES)
def test_create_database_invalid_pattern(case, raster_file, tmpworkdir):
    from terracotta.scripts import cli

    for infile in case['filenames']:
        temp_infile = tmpworkdir / infile
        os.makedirs(temp_infile.dirpath(), exist_ok=True)
        shutil.copy(raster_file, temp_infile)

    outfile = tmpworkdir / 'out.sqlite'
    input_pattern = case['input_pattern']

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['create-database', input_pattern, '-o', str(outfile)])
    assert result.exit_code != 0
    assert case['error_contains'].lower() in result.output.lower()


def test_create_database_rgb_key(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['create-database', input_pattern, '-o', str(outfile), '--rgb-key', 'rgb']
    )
    assert result.exit_code == 0
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == ('foo', 'rgb')
    assert driver.get_datasets() == {('g', 'i'): str(raster_file)}


def test_create_database_invalid_rgb_key(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['create-database', input_pattern, '-o', str(outfile), '--rgb-key', 'bar']
    )
    assert result.exit_code != 0
    assert not outfile.check()
