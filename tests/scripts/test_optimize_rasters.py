import warnings

import rasterio
import numpy as np

from click.testing import CliRunner

import pytest


@pytest.mark.parametrize('in_memory', [True, False, None])
def test_optimize_rasters(big_raster_file, tmpdir, in_memory):
    import validate_cloud_optimized_geotiff
    from terracotta.scripts import cli

    input_pattern = str(big_raster_file.dirpath('*.tif'))
    outfile = tmpdir / big_raster_file.basename

    runner = CliRunner()

    if in_memory is None:
        result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir)])
    else:
        in_memory_flag = '--in-memory' if in_memory else '--no-in-memory'
        result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', 
                                         str(tmpdir), in_memory_flag])

    assert result.exit_code == 0
    assert outfile.check()

    with rasterio.open(str(big_raster_file)) as src1, rasterio.open(str(outfile)) as src2:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', 'invalid value encountered.*')
            np.testing.assert_array_equal(src1.read(), src2.read())

    assert not validate_cloud_optimized_geotiff.cog_validate(str(big_raster_file))
    assert validate_cloud_optimized_geotiff.cog_validate(str(outfile))
