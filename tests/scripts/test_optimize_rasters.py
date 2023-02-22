import os
import warnings
import traceback

import rasterio
import numpy as np

from click.testing import CliRunner

import pytest


def format_exception(result):
    return ''.join(traceback.format_exception(*result.exc_info))


@pytest.fixture()
def tiny_raster_file(unoptimized_raster_file, tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp('tiny-raster')
    outfile = tmpdir / 'tiny.tif'
    with rasterio.open(str(unoptimized_raster_file)) as src:
        profile = src.profile.copy()
        profile.update(
            width=100,
            height=100,
            blockxsize=256,
            blockysize=256
        )

        with rasterio.open(str(outfile), 'w', **profile) as dst:
            dst.write(src.read()[:100, :100])

    yield outfile


@pytest.mark.parametrize('in_memory', [True, None, False])
@pytest.mark.parametrize('reproject', [True, False])
@pytest.mark.parametrize('compression', ['auto', 'lzw', 'none'])
@pytest.mark.parametrize('nproc', [None, 1, 2, -1])
def test_optimize_rasters(unoptimized_raster_file, tmpdir, in_memory,
                          reproject, compression, nproc):
    from terracotta.cog import validate
    from terracotta.scripts import cli

    input_pattern = str(unoptimized_raster_file.dirpath('*.tif'))
    outfile = tmpdir / unoptimized_raster_file.basename

    runner = CliRunner()

    flags = ['--compression', compression, '-q']

    if in_memory is not None:
        flags.append('--in-memory' if in_memory else '--no-in-memory')

    if reproject:
        flags.append('--reproject')

    if nproc is not None:
        flags.append(f'--nproc={nproc}')

    result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir), *flags])

    assert result.exit_code == 0, format_exception(result)
    assert outfile.check()

    # validate files
    assert not validate(str(unoptimized_raster_file))
    assert validate(str(outfile))

    if reproject:
        return

    # check for data integrity
    with rasterio.open(str(unoptimized_raster_file)) as src1, rasterio.open(str(outfile)) as src2:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', 'invalid value encountered.*')
            np.testing.assert_array_equal(src1.read(), src2.read())


def test_optimize_rasters_small(tiny_raster_file, tmpdir):
    from terracotta.cog import validate
    from terracotta.scripts import cli

    input_pattern = str(tiny_raster_file)
    outfile = tmpdir / tiny_raster_file.basename

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir)])

    assert result.exit_code == 0, format_exception(result)
    assert outfile.check()

    # validate files
    # (small rasters don't need overviews, so input file is valid, too)
    assert validate(str(tiny_raster_file))
    assert validate(str(outfile))

    # check for data integrity
    with rasterio.open(str(tiny_raster_file)) as src1, rasterio.open(str(outfile)) as src2:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', 'invalid value encountered.*')
            np.testing.assert_array_equal(src1.read(), src2.read())


def test_optimize_rasters_nofiles(tmpdir):
    from terracotta.scripts import cli

    input_pattern = str(tmpdir.dirpath('*.tif'))
    runner = CliRunner()
    result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir), '-q'])

    assert result.exit_code == 0
    assert 'No files given' in result.output


def test_optimize_rasters_invalid(tmpdir):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['optimize-rasters', str(tmpdir), '-o', str(tmpdir), '-q'])

    assert result.exit_code != 0
    assert 'not a file' in result.output

    result = runner.invoke(cli.cli, ['optimize-rasters', str(tmpdir), '-o', str(tmpdir),
                                     '--overwrite', '--skip-existing'])
    assert result.exit_code != 0
    assert 'mutually exclusive' in result.output


def test_optimize_rasters_multiband(tmpdir, unoptimized_raster_file):
    from terracotta.scripts import cli
    import rasterio

    with rasterio.open(str(unoptimized_raster_file)) as src:
        profile = src.profile.copy()
        data = src.read(1)

    profile['count'] = 3

    multiband_file = tmpdir.join(unoptimized_raster_file.basename)
    with rasterio.open(str(multiband_file), 'w', **profile) as dst:
        dst.write(data, 1)
        dst.write(data, 2)
        dst.write(data, 3)

    input_pattern = str(multiband_file.dirpath('*.tif'))
    outfile = tmpdir / 'co' / unoptimized_raster_file.basename

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ['optimize-rasters', input_pattern, '-o', str(tmpdir / 'co')]
    )

    assert result.exit_code == 0
    assert 'has more than one band' in result.output

    with rasterio.open(str(unoptimized_raster_file)) as src1, rasterio.open(str(outfile)) as src2:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', 'invalid value encountered.*')
            np.testing.assert_array_equal(src1.read(), src2.read())


@pytest.mark.parametrize('extra_flag', ['skip-existing', 'overwrite', None])
def test_reoptimize(tmpdir, unoptimized_raster_file, extra_flag):
    from terracotta.scripts import cli

    infile = str(unoptimized_raster_file.dirpath('*.tif'))
    outfile = tmpdir / 'out.tif'

    # first time
    runner = CliRunner()
    args = ['optimize-rasters', infile, '-o', str(outfile)]
    result = runner.invoke(cli.cli, args)
    assert result.exit_code == 0
    ctime = os.path.getmtime(outfile)

    # second time
    args = ['optimize-rasters', infile, '-o', str(outfile)]
    if extra_flag:
        args.append(f'--{extra_flag}')

    result = runner.invoke(cli.cli, args)

    if extra_flag == 'skip-existing':
        assert result.exit_code == 0
        assert os.path.getmtime(outfile) == ctime
    elif extra_flag == 'overwrite':
        assert result.exit_code == 0
        assert os.path.getmtime(outfile) != ctime
    else:
        assert result.exit_code == 2


def _throw(*args):
    raise RuntimeError('A mock error is raised')


def test_exception_in_subprocess(unoptimized_raster_file, tmpdir, monkeypatch):
    from terracotta.scripts import cli

    monkeypatch.setattr(
        'terracotta.scripts.optimize_rasters._optimize_single_raster',
        _throw
    )

    args = [
        'optimize-rasters', str(unoptimized_raster_file), '-o',
        str(tmpdir / 'foo.tif'), '--nproc', 2
    ]

    runner = CliRunner()
    result = runner.invoke(cli.cli, args)

    assert result.exit_code != 0
    assert 'Error while optimizing file' in str(result.exception)
