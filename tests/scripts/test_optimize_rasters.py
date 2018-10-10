import warnings

import rasterio
import numpy as np

from click.testing import CliRunner

import pytest


@pytest.mark.parametrize('in_memory', [True, False])
@pytest.mark.parametrize('reproject', [True, False])
def test_optimize_rasters(unoptimized_raster_file, tmpdir, in_memory, reproject):
    from terracotta.cog import validate
    from terracotta.scripts import cli

    input_pattern = str(unoptimized_raster_file.dirpath('*.tif'))
    outfile = tmpdir / unoptimized_raster_file.basename

    runner = CliRunner()

    flags = []
    if in_memory:
        flags.append('--in-memory')
    else:
        flags.append('--no-in-memory')

    if reproject:
        flags.append('--reproject')

    result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir), *flags])

    assert result.exit_code == 0
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


def test_optimize_rasters_nofiles(tmpdir):
    from terracotta.scripts import cli

    input_pattern = str(tmpdir.dirpath('*.tif'))
    runner = CliRunner()
    result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir)])

    assert result.exit_code == 0
    assert 'No files given' in result.output


def test_optimize_rasters_invalid(tmpdir):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['optimize-rasters', str(tmpdir), '-o', str(tmpdir)])

    assert result.exit_code != 0
    assert 'not a file' in result.output
