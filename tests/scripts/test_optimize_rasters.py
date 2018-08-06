import warnings

import rasterio
import numpy as np

from click.testing import CliRunner


def test_optimize_rasters(big_raster_file, tmpdir):
    import validate_cloud_optimized_geotiff
    from terracotta.scripts import cli

    input_pattern = str(big_raster_file.dirpath('*.tif'))
    outfile = tmpdir / big_raster_file.basename

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['optimize-rasters', input_pattern, '-o', str(tmpdir)])
    assert result.exit_code == 0
    assert outfile.check()

    with rasterio.open(str(big_raster_file)) as src1, rasterio.open(str(outfile)) as src2:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', 'invalid value encountered.*')
            np.testing.assert_array_equal(src1.read(), src2.read())

    assert not validate_cloud_optimized_geotiff.cog_validate(str(big_raster_file))
    assert validate_cloud_optimized_geotiff.cog_validate(str(outfile))
