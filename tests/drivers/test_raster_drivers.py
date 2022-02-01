import pytest

import platform
import time

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
    assert set(data1.keys()) == set(data2.keys())
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
        db.insert(['a', 'b'], '', skip_metadata=True)
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
@pytest.mark.parametrize('resampling_method', ['nearest', 'linear', 'cubic', 'average'])
def test_raster_retrieval(driver_path, provider, raster_file, resampling_method):
    import terracotta
    terracotta.update_settings(RESAMPLING_METHOD=resampling_method)

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

    assert len(db.raster_store._raster_cache) == 0

    data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256), asynchronous=asynchronous)

    if asynchronous:
        data1 = data1.result()
        time.sleep(1)  # allow callback to finish

    assert len(db.raster_store._raster_cache) == 1

    data2 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256), asynchronous=asynchronous)

    if asynchronous:
        data2 = data2.result()

    np.testing.assert_array_equal(data1, data2)
    assert len(db.raster_store._raster_cache) == 1


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

    assert len(db.raster_store._raster_cache) == 0

    data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256), asynchronous=asynchronous)

    if asynchronous:
        data1 = data1.result()
        time.sleep(1)  # allow callback to finish

    assert len(db.raster_store._raster_cache) == 0


@pytest.mark.parametrize('provider', DRIVERS)
def test_multiprocessing_fallback(driver_path, provider, raster_file, monkeypatch):
    import concurrent.futures
    from importlib import reload
    from terracotta import drivers
    import terracotta.drivers.geotiff_raster_store

    def dummy(*args, **kwargs):
        raise OSError('monkeypatched')

    try:
        with monkeypatch.context() as m, pytest.warns(UserWarning):
            m.setattr(concurrent.futures, 'ProcessPoolExecutor', dummy)

            reload(terracotta.drivers.geotiff_raster_store)
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
        reload(terracotta.drivers.geotiff_raster_store)


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


@pytest.mark.parametrize('provider', DRIVERS)
def test_broken_process_pool(driver_path, provider, raster_file):
    import concurrent.futures
    from terracotta import drivers
    from terracotta.drivers.geotiff_raster_store import context

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
    from terracotta.drivers.geotiff_raster_store import create_executor

    update_settings(USE_MULTIPROCESSING=False)

    executor = create_executor()
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)
