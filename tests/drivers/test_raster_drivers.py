import pytest

import platform
import time

import rasterio
import rasterio.features
from shapely.geometry import shape, MultiPolygon
import numpy as np

DRIVERS = ['sqlite', 'mysql']
METADATA_KEYS = ('bounds', 'range', 'mean', 'stdev', 'percentiles', 'metadata')


@pytest.mark.parametrize('provider', DRIVERS)
def test_insertion_and_retrieval(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))

    data = db.get_datasets()
    assert list(data.keys()) == [('some', 'value')]
    assert data[('some', 'value')] == str(raster_file)

    metadata = db.get_metadata(('some', 'value'))
    assert all(key in metadata for key in METADATA_KEYS)


@pytest.mark.parametrize('provider', DRIVERS)
def test_path_override(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')
    key_value = ('some', 'value')
    bogus_path = 'foo'

    db.create(keys)
    db.insert(key_value, str(raster_file), override_path=bogus_path)
    assert db.get_datasets()[key_value] == bogus_path

    with pytest.raises(IOError) as exc:
        # overridden path doesn't exist
        db.get_raster_tile(key_value)
        assert bogus_path in exc.value


@pytest.mark.parametrize('provider', DRIVERS)
def test_where(driver_path, provider, raster_file):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))
    db.insert({'some': 'a', 'keynames': 'third_value'}, str(raster_file))

    data = db.get_datasets()
    assert len(data) == 3

    data = db.get_datasets(where=dict(some='some'))
    assert len(data) == 2

    data = db.get_datasets(where=dict(some='some', keynames='value'))
    assert list(data.keys()) == [('some', 'value')]
    assert data[('some', 'value')] == str(raster_file)

    data = db.get_datasets(where=dict(some='unknown'))
    assert data == {}

    with pytest.raises(exceptions.InvalidKeyError) as exc:
        db.get_datasets(where=dict(unknown='foo'))
    assert 'unrecognized keys' in str(exc.value)


@pytest.mark.parametrize('provider', DRIVERS)
def test_where_with_multiquery(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))
    db.insert({'some': 'a', 'keynames': 'third_value'}, str(raster_file))

    data = db.get_datasets()
    assert len(data) == 3

    data = db.get_datasets(where=dict(some=['some']))
    assert len(data) == 2

    data = db.get_datasets(where=dict(keynames=['value', 'other_value']))
    assert len(data) == 2

    data = db.get_datasets(where=dict(some='some', keynames=['value', 'third_value']))
    assert list(data.keys()) == [('some', 'value')]
    assert data[('some', 'value')] == str(raster_file)

    data = db.get_datasets(where=dict(some=['unknown']))
    assert data == {}


@pytest.mark.parametrize('provider', DRIVERS)
def test_pagination(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))
    db.insert({'some': 'a', 'keynames': 'third_value'}, str(raster_file))

    data = db.get_datasets()
    assert len(data) == 3

    data = db.get_datasets(limit=2)
    assert len(data) == 2

    data = db.get_datasets(limit=2, page=1)
    assert len(data) == 1

    data = db.get_datasets(where=dict(some='some'), limit=1, page=0)
    assert len(data) == 1


@pytest.mark.parametrize('provider', DRIVERS)
def test_lazy_loading(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file), skip_metadata=False)
    db.insert(['some', 'other_value'], str(raster_file), skip_metadata=True)

    datasets = db.get_datasets()
    assert len(datasets) == 2

    data1 = db.get_metadata(['some', 'value'])
    data2 = db.get_metadata({'some': 'some', 'keynames': 'other_value'})
    assert list(data1.keys()) == list(data2.keys())
    assert all(np.all(data1[k] == data2[k]) for k in data1.keys())


@pytest.mark.parametrize('provider', DRIVERS)
def test_precomputed_metadata(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    metadata = db.compute_metadata(str(raster_file))

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file), metadata=metadata)
    db.insert(['some', 'other_value'], str(raster_file))

    datasets = db.get_datasets()
    assert len(datasets) == 2

    data1 = db.get_metadata(['some', 'value'])
    data2 = db.get_metadata({'some': 'some', 'keynames': 'other_value'})
    assert list(data1.keys()) == list(data2.keys())
    assert all(np.all(data1[k] == data2[k]) for k in data1.keys())


@pytest.mark.parametrize('provider', DRIVERS)
def test_invalid_insertion(monkeypatch, driver_path, provider, raster_file):
    from terracotta import drivers

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('keyname',)

    db.create(keys)

    def throw(*args, **kwargs):
        raise NotImplementedError()

    with monkeypatch.context() as m:
        m.setattr(db, 'compute_metadata', throw)

        db.insert(['bar'], str(raster_file), skip_metadata=True)

        with pytest.raises(NotImplementedError):
            db.insert(['foo'], str(raster_file), skip_metadata=False)

        datasets = db.get_datasets()

        assert ('bar',) in datasets
        assert ('foo',) not in datasets


@pytest.mark.parametrize('provider', DRIVERS)
def test_wrong_key_number(driver_path, provider, raster_file):
    from terracotta import drivers, exceptions

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('keyname',)

    db.create(keys)

    with pytest.raises(exceptions.InvalidKeyError) as exc:
        db.get_metadata(['a', 'b'])
    assert 'wrong number of keys' in str(exc.value)

    with pytest.raises(exceptions.InvalidKeyError) as exc:
        db.insert(['a', 'b'], '')
    assert 'wrong number of keys' in str(exc.value)

    with pytest.raises(exceptions.InvalidKeyError) as exc:
        db.delete(['a', 'b'])
    assert 'wrong number of keys' in str(exc.value)


@pytest.mark.parametrize('provider', DRIVERS)
def test_invalid_group_insertion(monkeypatch, driver_path, provider, raster_file):
    from terracotta import drivers

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('keyname',)

    db.create(keys)

    def throw(*args, **kwargs):
        raise NotImplementedError()

    with monkeypatch.context() as m:
        m.setattr(db, 'compute_metadata', throw)

        with db.connect():
            db.insert(['bar'], str(raster_file), skip_metadata=True)

            with pytest.raises(NotImplementedError):
                db.insert(['foo'], str(raster_file), skip_metadata=False)

            datasets = db.get_datasets()

        assert ('bar',) not in datasets
        assert ('foo',) not in datasets


def insertion_worker(key, path, raster_file, provider):
    import time
    from terracotta import drivers
    db = drivers.get_driver(path, provider=provider)
    with db.connect():
        db.insert([key], str(raster_file), skip_metadata=True)
        # keep connection open for a while to increase the chance of
        # triggering a race condition
        time.sleep(0.01)


@pytest.mark.xfail(platform.system() == "Darwin", reason="Flaky on OSX")
@pytest.mark.parametrize('provider', DRIVERS)
def test_multiprocess_insertion(driver_path, provider, raster_file):
    import functools
    import concurrent.futures
    from terracotta import drivers

    db = drivers.get_driver(driver_path, provider=provider)
    raster_file = str(raster_file)
    keys = ('keyname',)

    db.create(keys)

    key_vals = [str(i) for i in range(100)]

    worker = functools.partial(insertion_worker, path=driver_path, raster_file=raster_file,
                               provider=provider)

    with concurrent.futures.ProcessPoolExecutor(4) as executor:
        for _ in executor.map(worker, key_vals):
            pass

    datasets = db.get_datasets()
    assert all((key,) in datasets for key in key_vals)

    data1 = db.get_metadata(['77'])
    data2 = db.get_metadata({'keyname': '99'})
    assert list(data1.keys()) == list(data2.keys())
    assert all(np.all(data1[k] == data2[k]) for k in data1.keys())


@pytest.mark.parametrize('provider', DRIVERS)
def test_insertion_invalid_raster(driver_path, provider, invalid_raster_file):
    from terracotta import drivers

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('keyname',)

    db.create(keys)

    with pytest.raises(ValueError):
        db.insert(['val'], str(invalid_raster_file))

    datasets = db.get_datasets()
    assert ('val',) not in datasets


@pytest.mark.parametrize('provider', DRIVERS)
def test_raster_retrieval(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))

    data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256))
    assert data1.shape == (256, 256)

    data2 = db.get_raster_tile(['some', 'other_value'], tile_size=(256, 256))
    assert data2.shape == (256, 256)

    np.testing.assert_array_equal(data1, data2)


@pytest.mark.parametrize('provider', DRIVERS)
@pytest.mark.parametrize('asynchronous', [True, False])
def test_raster_cache(driver_path, provider, raster_file, asynchronous):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))

    assert len(db._raster_cache) == 0

    data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256), asynchronous=asynchronous)

    if asynchronous:
        data1 = data1.result()
        time.sleep(1)  # allow callback to finish

    assert len(db._raster_cache) == 1

    data2 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256), asynchronous=asynchronous)

    if asynchronous:
        data2 = data2.result()

    np.testing.assert_array_equal(data1, data2)
    assert len(db._raster_cache) == 1


@pytest.mark.parametrize('provider', DRIVERS)
@pytest.mark.parametrize('asynchronous', [True, False])
def test_raster_cache_fail(driver_path, provider, raster_file, asynchronous):
    """Retrieve a tile that is larger than the total cache size"""
    from terracotta import drivers, update_settings
    update_settings(RASTER_CACHE_SIZE=1)

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))

    assert len(db._raster_cache) == 0

    data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256), asynchronous=asynchronous)

    if asynchronous:
        data1 = data1.result()
        time.sleep(1)  # allow callback to finish

    assert len(db._raster_cache) == 0


@pytest.mark.parametrize('provider', DRIVERS)
def test_multiprocessing_fallback(driver_path, provider, raster_file, monkeypatch):
    import concurrent.futures
    from importlib import reload
    from terracotta import drivers
    import terracotta.drivers.raster_base

    def dummy(*args, **kwargs):
        raise OSError('monkeypatched')

    try:
        with monkeypatch.context() as m, pytest.warns(UserWarning):
            m.setattr(concurrent.futures, 'ProcessPoolExecutor', dummy)

            reload(terracotta.drivers.raster_base)
            db = drivers.get_driver(driver_path, provider=provider)
            keys = ('some', 'keynames')

            db.create(keys)
            db.insert(['some', 'value'], str(raster_file))
            db.insert(['some', 'other_value'], str(raster_file))

            data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256))
            assert data1.shape == (256, 256)

            data2 = db.get_raster_tile(['some', 'other_value'], tile_size=(256, 256))
            assert data2.shape == (256, 256)

            np.testing.assert_array_equal(data1, data2)
    finally:
        reload(terracotta.drivers.raster_base)


@pytest.mark.parametrize('provider', DRIVERS)
def test_raster_duplicate(driver_path, provider, raster_file):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'value'], str(raster_file))

    assert list(db.get_datasets().keys()) == [('some', 'value')]


@pytest.mark.parametrize('provider', DRIVERS)
def test_deletion(driver_path, provider, raster_file):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)

    dataset = {'some': 'some', 'keynames': 'value'}
    db.insert(dataset, str(raster_file))

    data = db.get_datasets()
    assert list(data.keys()) == [('some', 'value')]
    assert data[('some', 'value')] == str(raster_file)

    metadata = db.get_metadata(('some', 'value'))
    assert all(key in metadata for key in METADATA_KEYS)

    db.delete(dataset)
    assert not db.get_datasets()

    with pytest.raises(exceptions.DatasetNotFoundError):
        db.get_metadata(dataset)


@pytest.mark.parametrize('provider', DRIVERS)
def test_delete_nonexisting(driver_path, provider, raster_file):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)

    dataset = {'some': 'some', 'keynames': 'value'}

    with pytest.raises(exceptions.DatasetNotFoundError):
        db.delete(dataset)


@pytest.mark.parametrize('provider', DRIVERS)
def test_nodata_consistency(driver_path, provider, big_raster_file_mask, big_raster_file_nodata):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('type',)

    db.create(keys)
    db.insert(['mask'], str(big_raster_file_mask), skip_metadata=True)
    db.insert(['nodata'], str(big_raster_file_nodata), skip_metadata=True)

    data_mask = db.get_raster_tile(['mask'])
    data_nodata = db.get_raster_tile(['nodata'])

    np.testing.assert_array_equal(data_mask.mask, data_nodata.mask)


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


@pytest.mark.parametrize('use_chunks', [True, False])
@pytest.mark.parametrize('nodata_type', ['nodata', 'masked', 'none', 'nan'])
def test_compute_metadata(big_raster_file_nodata, big_raster_file_nomask,
                          big_raster_file_mask, raster_file_float, nodata_type, use_chunks):
    from terracotta.drivers.raster_base import RasterDriver

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
            mtd = RasterDriver.compute_metadata(str(raster_file), use_chunks=use_chunks)
            assert 'does not have a valid nodata value' in str(record[0].message)
    else:
        mtd = RasterDriver.compute_metadata(str(raster_file), use_chunks=use_chunks)

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
    from terracotta.drivers.raster_base import RasterDriver

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
            mtd = RasterDriver.compute_metadata(str(raster_file), max_shape=(512, 512))
            assert 'does not have a valid nodata value' in str(record[0].message)
    else:
        mtd = RasterDriver.compute_metadata(str(raster_file), max_shape=(512, 512))

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
    from terracotta.drivers.raster_base import RasterDriver

    with pytest.raises(ValueError):
        RasterDriver.compute_metadata(
            str(big_raster_file_nodata), max_shape=(256, 256), use_chunks=True
        )

    with pytest.raises(ValueError):
        RasterDriver.compute_metadata(str(big_raster_file_nodata), max_shape=(256, 256, 1))


@pytest.mark.parametrize('use_chunks', [True, False])
def test_compute_metadata_invalid_raster(invalid_raster_file, use_chunks):
    from terracotta.drivers.raster_base import RasterDriver

    if use_chunks:
        pytest.importorskip('crick')

    with pytest.raises(ValueError):
        RasterDriver.compute_metadata(str(invalid_raster_file), use_chunks=use_chunks)


def test_compute_metadata_nocrick(big_raster_file_nodata, monkeypatch):
    with rasterio.open(str(big_raster_file_nodata)) as src:
        data = src.read(1, masked=True)
        valid_data = np.ma.masked_invalid(data).compressed()
        convex_hull = convex_hull_exact(src)

    from terracotta import exceptions
    import terracotta.drivers.raster_base

    with monkeypatch.context() as m:
        m.setattr(terracotta.drivers.raster_base, 'has_crick', False)

        with pytest.warns(exceptions.PerformanceWarning):
            mtd = terracotta.drivers.raster_base.RasterDriver.compute_metadata(
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
    from terracotta.drivers.raster_base import RasterDriver

    with rasterio.open(str(unoptimized_raster_file)) as src:
        data = src.read(1, masked=True)
        valid_data = np.ma.masked_invalid(data).compressed()
        convex_hull = convex_hull_exact(src)

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

    assert geometry_mismatch(shape(mtd['convex_hull']), convex_hull) < 1e-6


@pytest.mark.parametrize('provider', DRIVERS)
def test_broken_process_pool(driver_path, provider, raster_file):
    import concurrent.futures
    from terracotta import drivers
    from terracotta.drivers.raster_base import context

    class BrokenPool:
        def submit(self, *args, **kwargs):
            raise concurrent.futures.process.BrokenProcessPool('monkeypatched')

    context.executor = BrokenPool()

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))

    data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256))
    assert data1.shape == (256, 256)

    data2 = db.get_raster_tile(['some', 'other_value'], tile_size=(256, 256))
    assert data2.shape == (256, 256)

    np.testing.assert_array_equal(data1, data2)


def test_no_multiprocessing():
    import concurrent.futures
    from terracotta import update_settings
    from terracotta.drivers.raster_base import create_executor

    update_settings(USE_MULTIPROCESSING=False)

    executor = create_executor()
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)
