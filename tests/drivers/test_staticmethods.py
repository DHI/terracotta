import pytest


def test_safe_transform_oom():
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

    with pytest.raises(CPLE_OutOfMemoryError):
        rio_transform, rio_width, rio_height = calculate_default_transform(*args)

    our_transform, our_width, our_height = RasterDriver._calculate_default_transform(*args)

    assert our_width == args[2]
    assert our_height == args[3]



