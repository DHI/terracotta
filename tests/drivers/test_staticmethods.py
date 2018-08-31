import pytest


def test_default_transform():
    from rasterio.warp import calculate_default_transform
    from rasterio._err import CPLE_OutOfMemoryError

    from terracotta.drivers.raster_base import RasterDriver

    args = (
        'epsg:4326',
        'epsg:4326',
        2 * 10**6,
        10**6,
        -10, -10, 10, 10
    )

    # we can handle cases rasterio can't
    with pytest.raises(CPLE_OutOfMemoryError):
        rio_transform, rio_width, rio_height = calculate_default_transform(*args)

    our_transform, our_width, our_height = RasterDriver._calculate_default_transform(*args)

    assert our_width == args[2]
    assert our_height == args[3]


@pytest.mark.parametrize('use_chunks', [True, False])
def test_compute_metadata(big_raster_file, use_chunks):
    import rasterio
    import numpy as np

    from terracotta.drivers.raster_base import RasterDriver

    with rasterio.open(str(big_raster_file)) as src:
        data = src.read(1)
        data = data[np.isfinite(data) & (data != src.nodata)]

    mtd = RasterDriver.compute_metadata(str(big_raster_file), use_chunks=use_chunks)

    np.testing.assert_allclose(mtd['range'], (data.min(), data.max()))
    np.testing.assert_allclose(mtd['mean'], data.mean())
    np.testing.assert_allclose(mtd['stdev'], data.std())

    # allow error of 1%
    np.testing.assert_allclose(
        mtd['percentiles'], 
        np.percentile(data, np.arange(1, 100)),
        rtol=0.01
    )
