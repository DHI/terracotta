import warnings

import rasterio
import numpy as np

from click.testing import CliRunner

import pytest


@pytest.mark.parametrize('in_memory', [True, None, False])
@pytest.mark.parametrize('reproject', [True, False])
@pytest.mark.parametrize('compression', ['auto', 'lzw', 'none'])
def test_optimize_rasters(unoptimized_raster_file, tmpdir, in_memory, reproject, compression):
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
    result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir), '-q'])

    assert result.exit_code == 0
    assert 'No files given' in result.output


def test_optimize_rasters_invalid(tmpdir):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['optimize-rasters', str(tmpdir), '-o', str(tmpdir), '-q'])

    assert result.exit_code != 0
    assert 'not a file' in result.output


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
