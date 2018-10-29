import numpy as np
import pytest

DRIVERS = ['sqlite', 'mysql']
METADATA_KEYS = ('bounds', 'nodata', 'range', 'mean', 'stdev', 'percentiles', 'metadata')


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
def test_where(driver_path, provider, raster_file):
    from terracotta import drivers
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
        for result in executor.map(worker, key_vals):
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
@pytest.mark.parametrize('native_crs', [True, False])
def test_raster_retrieval(driver_path, provider, raster_file, raster_file_3857, native_crs):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    if native_crs:
        raster_file = raster_file_3857

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))

    data1 = db.get_raster_tile(['some', 'value'], tile_size=(256, 256))
    assert data1.shape == (256, 256)

    data2 = db.get_raster_tile(['some', 'other_value'], tile_size=(256, 256))
    assert data2.shape == (256, 256)

    np.testing.assert_array_equal(data1, data2)


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
