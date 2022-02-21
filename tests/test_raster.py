import pytest

import numpy as np
import rasterio
import rasterio.features
from shapely.geometry import shape, MultiPolygon


def geometry_mismatch(shape1, shape2):
    """Compute relative mismatch of two shapes"""
    return shape1.symmetric_difference(shape2).area / shape1.union(shape2).area


def convex_hull_exact(src):
    kwargs = dict(bidx=1, band=False, as_mask=True, geographic=True)

    data = src.read()
    if np.any(np.isnan(data)) and src.nodata is not None:
        # hack: replace NaNs with nodata to make sure they are excluded
        with rasterio.MemoryFile() as memfile, memfile.open(**src.profile) as tmpsrc:
            data[np.isnan(data)] = src.nodata
            tmpsrc.write(data)
            dataset_shape = list(rasterio.features.dataset_features(tmpsrc, **kwargs))
    else:
        dataset_shape = list(rasterio.features.dataset_features(src, **kwargs))

    convex_hull = MultiPolygon([shape(s['geometry']) for s in dataset_shape]).convex_hull
    return convex_hull


@pytest.mark.parametrize('large_raster_threshold', [None, 0])
@pytest.mark.parametrize('use_chunks', [True, False, None])
@pytest.mark.parametrize('nodata_type', ['nodata', 'masked', 'none', 'nan'])
def test_compute_metadata(big_raster_file_nodata, big_raster_file_nomask, big_raster_file_mask,
                          raster_file_float, nodata_type, use_chunks, large_raster_threshold):
    from terracotta import raster

    if nodata_type == 'nodata':
        raster_file = big_raster_file_nodata
    elif nodata_type == 'masked':
        raster_file = big_raster_file_mask
    elif nodata_type == 'none':
        raster_file = big_raster_file_nomask
    elif nodata_type == 'nan':
        raster_file = raster_file_float

    if use_chunks:
        pytest.importorskip('crick')

    with rasterio.open(str(raster_file)) as src:
        data = src.read(1, masked=True)
        valid_data = np.ma.masked_invalid(data).compressed()
        convex_hull = convex_hull_exact(src)

    # compare
    if nodata_type == 'none':
        with pytest.warns(UserWarning) as record:
            mtd = raster.compute_metadata(
                str(raster_file),
                use_chunks=use_chunks,
                large_raster_threshold=large_raster_threshold
            )
            assert 'does not have a valid nodata value' in str(record[0].message)
    else:
        mtd = raster.compute_metadata(
            str(raster_file),
            use_chunks=use_chunks,
            large_raster_threshold=large_raster_threshold
        )

    np.testing.assert_allclose(mtd['valid_percentage'], 100 * valid_data.size / data.size)
    np.testing.assert_allclose(mtd['range'], (valid_data.min(), valid_data.max()))
    np.testing.assert_allclose(mtd['mean'], valid_data.mean())
    np.testing.assert_allclose(mtd['stdev'], valid_data.std())

    # allow some error margin since we only compute approximate quantiles
    np.testing.assert_allclose(
        mtd['percentiles'],
        np.percentile(valid_data, np.arange(1, 100)),
        rtol=2e-2, atol=valid_data.max() / 100
    )

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 1e-6


@pytest.mark.parametrize('nodata_type', ['nodata', 'masked', 'none', 'nan'])
def test_compute_metadata_approximate(nodata_type, big_raster_file_nodata, big_raster_file_mask,
                                      big_raster_file_nomask, raster_file_float):
    from terracotta import raster

    if nodata_type == 'nodata':
        raster_file = big_raster_file_nodata
    elif nodata_type == 'masked':
        raster_file = big_raster_file_mask
    elif nodata_type == 'none':
        raster_file = big_raster_file_nomask
    elif nodata_type == 'nan':
        raster_file = raster_file_float

    with rasterio.open(str(raster_file)) as src:
        data = src.read(1, masked=True)
        valid_data = np.ma.masked_invalid(data).compressed()
        convex_hull = convex_hull_exact(src)

    # compare
    if nodata_type == 'none':
        with pytest.warns(UserWarning) as record:
            mtd = raster.compute_metadata(str(raster_file), max_shape=(512, 512))
            assert 'does not have a valid nodata value' in str(record[0].message)
    else:
        mtd = raster.compute_metadata(str(raster_file), max_shape=(512, 512))

    np.testing.assert_allclose(mtd['valid_percentage'], 100 * valid_data.size / data.size, atol=1)
    np.testing.assert_allclose(
        mtd['range'], (valid_data.min(), valid_data.max()), atol=valid_data.max() / 100
    )
    np.testing.assert_allclose(mtd['mean'], valid_data.mean(), rtol=0.02)
    np.testing.assert_allclose(mtd['stdev'], valid_data.std(), rtol=0.02)

    np.testing.assert_allclose(
        mtd['percentiles'],
        np.percentile(valid_data, np.arange(1, 100)),
        atol=valid_data.max() / 100, rtol=0.02
    )

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 0.05


def test_compute_metadata_invalid_options(big_raster_file_nodata):
    from terracotta import raster

    with pytest.raises(ValueError):
        raster.compute_metadata(
            str(big_raster_file_nodata), max_shape=(256, 256), use_chunks=True
        )

    with pytest.raises(ValueError):
        raster.compute_metadata(str(big_raster_file_nodata), max_shape=(256, 256, 1))


@pytest.mark.parametrize('use_chunks', [True, False])
def test_compute_metadata_invalid_raster(invalid_raster_file, use_chunks):
    from terracotta import raster

    if use_chunks:
        pytest.importorskip('crick')

    with pytest.raises(ValueError):
        raster.compute_metadata(str(invalid_raster_file), use_chunks=use_chunks)


def test_compute_metadata_nocrick(big_raster_file_nodata, monkeypatch):
    with rasterio.open(str(big_raster_file_nodata)) as src:
        data = src.read(1, masked=True)
        valid_data = np.ma.masked_invalid(data).compressed()
        convex_hull = convex_hull_exact(src)

    from terracotta import exceptions
    import terracotta.drivers.geotiff_raster_store

    with monkeypatch.context() as m:
        m.setattr(terracotta.raster, 'has_crick', False)

        with pytest.warns(exceptions.PerformanceWarning):
            mtd = terracotta.drivers.geotiff_raster_store.raster.compute_metadata(
                str(big_raster_file_nodata), use_chunks=True
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

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 1e-6


def test_compute_metadata_unoptimized(unoptimized_raster_file):
    from terracotta import exceptions
    from terracotta import raster

    with rasterio.open(str(unoptimized_raster_file)) as src:
        data = src.read(1, masked=True)
        valid_data = np.ma.masked_invalid(data).compressed()
        convex_hull = convex_hull_exact(src)

    # compare
    with pytest.warns(exceptions.PerformanceWarning):
        mtd = raster.compute_metadata(str(unoptimized_raster_file), use_chunks=False)

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

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 1e-6


@pytest.mark.parametrize('preserve_values', [True, False])
@pytest.mark.parametrize('resampling_method', ['nearest', 'linear', 'cubic', 'average'])
def test_get_raster_tile(raster_file, preserve_values, resampling_method):
    from terracotta import raster

    data = raster.get_raster_tile(
        str(raster_file),
        reprojection_method=resampling_method,
        resampling_method=resampling_method,
        preserve_values=preserve_values,
        tile_size=(256, 256)
    )
    assert data.shape == (256, 256)


def test_get_raster_tile_out_of_bounds(raster_file):
    from terracotta import exceptions
    from terracotta import raster

    bounds = (
        -1e30,
        -1e30,
        1e30,
        1e30,
    )

    with pytest.raises(exceptions.TileOutOfBoundsError):
        raster.get_raster_tile(str(raster_file), tile_bounds=bounds)


def test_get_raster_no_nodata(big_raster_file_nomask):
    from terracotta import raster

    tile_size = (256, 256)
    out = raster.get_raster_tile(str(big_raster_file_nomask), tile_size=tile_size)
    assert out.shape == tile_size


def test_invalid_resampling_method():
    from terracotta import raster

    with pytest.raises(ValueError) as exc:
        raster.get_resampling_enum('not-a-resampling-method')
    assert 'unknown resampling method' in str(exc)
