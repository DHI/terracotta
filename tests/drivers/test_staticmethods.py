import pytest

import rasterio
import rasterio.features
from shapely.geometry import shape, MultiPolygon
import numpy as np


def test_default_transform():
    from rasterio.warp import calculate_default_transform

    from terracotta.drivers.raster_base import RasterDriver

    args = (
        'epsg:4326',
        'epsg:4326',
        2 * 10**6,
        10**6,
        -10, -10, 10, 10
    )

    # GDAL defaults don't round-trip non-square pixels
    _, rio_width, rio_height = calculate_default_transform(*args)
    assert rio_width != args[2]
    assert rio_height != args[3]

    # we do!
    our_transform, our_width, our_height = RasterDriver._calculate_default_transform(*args)
    assert our_width == args[2]
    assert our_height == args[3]


def geometry_mismatch(shape1, shape2):
    """Compute relative mismatch of two shapes"""
    return shape1.symmetric_difference(shape2).area / shape1.union(shape2).area


@pytest.mark.parametrize('use_chunks', [True, False])
def test_compute_metadata(big_raster_file, use_chunks):
    from terracotta.drivers.raster_base import RasterDriver

    if use_chunks:
        pytest.importorskip('crick')

    with rasterio.open(str(big_raster_file)) as src:
        data = src.read(1)
        valid_data = data[np.isfinite(data) & (data != src.nodata)]
        dataset_shape = list(rasterio.features.dataset_features(
            src, bidx=1, as_mask=True, geographic=True
        ))

    convex_hull = MultiPolygon([shape(s['geometry']) for s in dataset_shape]).convex_hull

    # compare
    mtd = RasterDriver.compute_metadata(str(big_raster_file), use_chunks=use_chunks)

    np.testing.assert_allclose(mtd['valid_percentage'], 100 * valid_data.size / data.size)
    np.testing.assert_allclose(mtd['range'], (valid_data.min(), valid_data.max()))
    np.testing.assert_allclose(mtd['mean'], valid_data.mean())
    np.testing.assert_allclose(mtd['stdev'], valid_data.std())

    # allow some error margin since we only compute approximate quantiles
    np.testing.assert_allclose(
        mtd['percentiles'],
        np.percentile(valid_data, np.arange(1, 100)),
        rtol=2e-2
    )

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 1e-8


def test_compute_metadata_approximate(big_raster_file):
    from terracotta.drivers.raster_base import RasterDriver

    with rasterio.open(str(big_raster_file)) as src:
        data = src.read(1)
        valid_data = data[np.isfinite(data) & (data != src.nodata)]
        dataset_shape = list(rasterio.features.dataset_features(
            src, bidx=1, as_mask=True, geographic=True
        ))

    convex_hull = MultiPolygon([shape(s['geometry']) for s in dataset_shape]).convex_hull

    # compare
    mtd = RasterDriver.compute_metadata(str(big_raster_file), max_shape=(512, 512))

    np.testing.assert_allclose(mtd['valid_percentage'], 100 * valid_data.size / data.size, atol=1)
    np.testing.assert_allclose(
        mtd['range'], (valid_data.min(), valid_data.max()), atol=valid_data.max() / 100
    )
    np.testing.assert_allclose(mtd['mean'], valid_data.mean(), rtol=0.02)
    np.testing.assert_allclose(mtd['stdev'], valid_data.std(), rtol=0.02)

    np.testing.assert_allclose(
        mtd['percentiles'],
        np.percentile(valid_data, np.arange(1, 100)),
        atol=valid_data.max() / 100, rtol=0.05
    )

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 0.1


def test_compute_metadata_invalid_options(big_raster_file):
    from terracotta.drivers.raster_base import RasterDriver

    with pytest.raises(ValueError):
        RasterDriver.compute_metadata(str(big_raster_file), max_shape=(256, 256), use_chunks=True)

    with pytest.raises(ValueError):
        RasterDriver.compute_metadata(str(big_raster_file), max_shape=(256, 256, 1))


@pytest.mark.parametrize('use_chunks', [True, False])
def test_compute_metadata_invalid_raster(invalid_raster_file, use_chunks):
    from terracotta.drivers.raster_base import RasterDriver

    if use_chunks:
        pytest.importorskip('crick')

    with pytest.raises(ValueError):
        RasterDriver.compute_metadata(str(invalid_raster_file), use_chunks=use_chunks)


def test_compute_metadata_nocrick(big_raster_file, monkeypatch):
    with rasterio.open(str(big_raster_file)) as src:
        data = src.read(1)
        valid_data = data[np.isfinite(data) & (data != src.nodata)]
        dataset_shape = list(rasterio.features.dataset_features(
            src, bidx=1, as_mask=True, geographic=True
        ))

    convex_hull = MultiPolygon([shape(s['geometry']) for s in dataset_shape]).convex_hull

    from terracotta import exceptions
    import terracotta.drivers.raster_base

    with monkeypatch.context() as m:
        m.setattr(terracotta.drivers.raster_base, 'has_crick', False)

        with pytest.warns(exceptions.PerformanceWarning):
            mtd = terracotta.drivers.raster_base.RasterDriver.compute_metadata(
                str(big_raster_file), use_chunks=True
            )

    # compare
    np.testing.assert_allclose(mtd['valid_percentage'], 100 * valid_data.size / data.size)
    np.testing.assert_allclose(mtd['range'], (valid_data.min(), valid_data.max()))
    np.testing.assert_allclose(mtd['mean'], valid_data.mean())
    np.testing.assert_allclose(mtd['stdev'], valid_data.std())

    # allow error of 1%, since we only compute approximate quantiles
    np.testing.assert_allclose(
        mtd['percentiles'],
        np.percentile(valid_data, np.arange(1, 100)),
        rtol=2e-2
    )

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 1e-8


def test_compute_metadata_unoptimized(unoptimized_raster_file):
    from terracotta import exceptions
    from terracotta.drivers.raster_base import RasterDriver

    with rasterio.open(str(unoptimized_raster_file)) as src:
        data = src.read(1)
        valid_data = data[np.isfinite(data) & (data != src.nodata)]
        dataset_shape = list(rasterio.features.dataset_features(
            src, bidx=1, as_mask=True, geographic=True
        ))

    convex_hull = MultiPolygon([shape(s['geometry']) for s in dataset_shape]).convex_hull

    # compare
    with pytest.warns(exceptions.PerformanceWarning):
        mtd = RasterDriver.compute_metadata(str(unoptimized_raster_file), use_chunks=False)

    np.testing.assert_allclose(mtd['valid_percentage'], 100 * valid_data.size / data.size)
    np.testing.assert_allclose(mtd['range'], (valid_data.min(), valid_data.max()))
    np.testing.assert_allclose(mtd['mean'], valid_data.mean())
    np.testing.assert_allclose(mtd['stdev'], valid_data.std())

    # allow some error margin since we only compute approximate quantiles
    np.testing.assert_allclose(
        mtd['percentiles'],
        np.percentile(valid_data, np.arange(1, 100)),
        rtol=2e-2
    )

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 1e-8
