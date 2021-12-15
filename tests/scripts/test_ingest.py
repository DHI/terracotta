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
    {  # case-sensitivity
        'filenames': ['bAr.tif', 'FOO.tif'],
        'input_pattern': '{nAmE}.tif',
        'expected_keys': ['nAmE'],
        'expected_datasets': [('bAr',), ('FOO',)]
    },
    {  # unicode path with space
        'filenames': ['süßer ordner/foo.tif'],
        'input_pattern': '{}/{name}.tif',
        'expected_keys': ['name'],
        'expected_datasets': [('foo',)]
    },
    {  # unicode key
        'filenames': ['günther.tif'],
        'input_pattern': '{bärbel}.tif',
        'expected_keys': ['bärbel'],
        'expected_datasets': [('günther',)]
    },
)

INVALID_TEST_CASES = (
    {  # no matching files
        'filenames': [],
        'input_pattern': '{key}.tif',
        'error_contains': 'matches no files'
    },
    {  # duplicate keys in different folders
        'filenames': ['dir1/foo.tif', 'dir2/foo.tif'],
        'input_pattern': '{}/{name}.tif',
        'error_contains': 'duplicate keys'
    },
    {  # duplicate keys through wildcard
        'filenames': ['S2_B04.tif', 'S2_20180101_B04.tif'],
        'input_pattern': '{sensor}_{}.tif',
        'error_contains': 'duplicate keys'
    },
    {  # no groups in pattern
        'filenames': [],
        'input_pattern': 'notafile.tif',
        'error_contains': 'at least one placeholder'
    },
    {  # only wildcards in pattern
        'filenames': [],
        'input_pattern': '{}.tif',
        'error_contains': 'at least one placeholder'
    },
    {  # stray {
        'filenames': [],
        'input_pattern': 'notafile{.tif',
        'error_contains': 'invalid pattern'
    },
    {  # invalid placeholder name
        'filenames': ['foo.tif'],
        'input_pattern': '{(foo)}.tif',
        'error_contains': 'must be alphanumeric'
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


def test_ingest(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{name}.tif'))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['ingest', input_pattern, '-o', str(outfile)])
    assert result.exit_code == 0
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == ('name',)
    assert driver.get_datasets() == {('img',): str(raster_file)}


def test_ingest_append(raster_file, tmpworkdir):
    from terracotta.scripts import cli

    for infile in ('dir1/img1.tif', 'dir2/img2.tif'):
        temp_infile = tmpworkdir / infile
        os.makedirs(temp_infile.dirpath(), exist_ok=True)
        shutil.copy(raster_file, temp_infile)

    outfile = tmpworkdir / 'out.sqlite'

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['ingest', 'dir1/{name}.tif', '-o', str(outfile)])
    assert result.exit_code == 0
    assert outfile.check()

    result = runner.invoke(cli.cli, ['ingest', 'dir2/{name}.tif', '-o', str(outfile)])
    assert result.exit_code == 0
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == ('name',)
    assert all((ds,) in driver.get_datasets() for ds in ('img1', 'img2'))


@pytest.mark.parametrize('skip_existing', [True, False])
def test_reingest(skip_existing, raster_file, tmpworkdir):
    from terracotta.scripts import cli
    from terracotta import get_driver

    same_name = 'myimage'
    infiles = [
        tmpworkdir / p
        for p in [f'dir1/{same_name}.tif', f'dir2/{same_name}.tif', f'dir3/{same_name}.tif']
    ]
    for temp_infile in infiles:
        os.makedirs(temp_infile.dirpath(), exist_ok=True)
        shutil.copy(raster_file, temp_infile)

    outfile = tmpworkdir / 'out.sqlite'

    def _assert_datasets_equal(datasets):
        assert outfile.check()
        driver = get_driver(str(outfile), provider='sqlite')
        existing_datasets = driver.get_datasets()
        assert len(existing_datasets) == 1
        assert existing_datasets == datasets

    runner = CliRunner()
    args = ['ingest', 'dir1/{name}.tif', '-o', str(outfile)]
    result = runner.invoke(cli.cli, args)
    assert result.exit_code == 0
    _assert_datasets_equal({(same_name,): str(infiles[0])})

    args = ['ingest', 'dir2/{name}.tif', '-o', str(outfile)]
    if skip_existing:
        args.append("--skip-existing")
    result = runner.invoke(cli.cli, args)
    assert result.exit_code == 0
    if skip_existing:
        _assert_datasets_equal({(same_name,): str(infiles[0])})
    else:
        _assert_datasets_equal({(same_name,): str(infiles[1])})

    args = ['ingest', 'dir3/{name}.tif', '-o', str(outfile)]
    if skip_existing:
        args.append("--skip-existing")
    result = runner.invoke(cli.cli, args)
    assert result.exit_code == 0
    if skip_existing:
        _assert_datasets_equal({(same_name,): str(infiles[0])})
    else:
        _assert_datasets_equal({(same_name,): str(infiles[2])})


def test_ingest_append_invalid(raster_file, tmpworkdir):
    from terracotta.scripts import cli

    for infile in ('dir1/img1.tif', 'dir2/img2.tif'):
        temp_infile = tmpworkdir / infile
        os.makedirs(temp_infile.dirpath(), exist_ok=True)
        shutil.copy(raster_file, temp_infile)

    outfile = tmpworkdir / 'out.sqlite'

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['ingest', 'dir1/{name}.tif', '-o', str(outfile)])
    assert result.exit_code == 0
    assert outfile.check()

    result = runner.invoke(cli.cli, ['ingest', '{dir}/{name}.tif', '-o', str(outfile)])
    assert result.exit_code != 0
    assert 'incompatible key names' in result.output


@pytest.mark.parametrize('case', TEST_CASES)
@pytest.mark.parametrize('abspath', [True, False])
def test_ingest_pattern(case, abspath, raster_file, tmpworkdir):
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
    result = runner.invoke(cli.cli, ['ingest', input_pattern, '-o', str(outfile)])
    assert result.exit_code == 0, result.output
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == tuple(case['expected_keys'])
    assert all(ds in driver.get_datasets() for ds in case['expected_datasets'])


@pytest.mark.parametrize('case', INVALID_TEST_CASES)
def test_ingest_invalid_pattern(case, raster_file, tmpworkdir):
    from terracotta.scripts import cli

    for infile in case['filenames']:
        temp_infile = tmpworkdir / infile
        os.makedirs(temp_infile.dirpath(), exist_ok=True)
        shutil.copy(raster_file, temp_infile)

    outfile = tmpworkdir / 'out.sqlite'
    input_pattern = case['input_pattern']

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['ingest', input_pattern, '-o', str(outfile)])
    assert result.exit_code != 0
    assert case['error_contains'].lower() in result.output.lower()


def test_ingest_rgb_key(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['ingest', input_pattern, '-o', str(outfile), '--rgb-key', 'rgb']
    )
    assert result.exit_code == 0
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == ('foo', 'rgb')
    assert driver.get_datasets() == {('g', 'i'): str(raster_file)}


def test_ingest_invalid_rgb_key(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['ingest', input_pattern, '-o', str(outfile), '--rgb-key', 'bar']
    )
    assert result.exit_code != 0
    assert not outfile.check()
