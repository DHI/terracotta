import numpy as np
import pytest


DRIVERS = ['sqlite']

METADATA_KEYS = ('bounds', 'nodata', 'range', 'mean', 'stdev', 'percentiles', 'metadata')


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation(tmpdir, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')
    db.create(keys)

    assert db.available_keys == keys
    assert db.get_datasets() == {}
    assert dbfile.isfile()


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid(tmpdir, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('invalid key')

    with pytest.raises(ValueError):
        db.create(keys)


@pytest.mark.parametrize('provider', DRIVERS)
def test_connect(tmpdir, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')

    with db.connect():
        db.create(keys)

    assert db.available_keys == keys
    assert db.get_datasets() == {}
    assert dbfile.isfile()


@pytest.mark.parametrize('provider', DRIVERS)
def test_recreation(tmpdir, provider):
    from terracotta import drivers, exceptions
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')

    db.create(keys)
    assert db.available_keys == keys
    assert db.get_datasets() == {}

    with pytest.raises(exceptions.InvalidDatabaseError):
        db.create(keys, drop_if_exists=False)

    db.create(keys, drop_if_exists=True)
    assert db.available_keys == keys
    assert db.get_datasets() == {}


@pytest.mark.parametrize('provider', DRIVERS)
def test_insertion_and_retrieval(tmpdir, raster_file, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))

    data = db.get_datasets()
    assert list(data.keys()) == [('some', 'value')]
    assert data[('some', 'value')] == str(raster_file)

    metadata = db.get_metadata(('some', 'value'))
    assert all(key in metadata for key in METADATA_KEYS)


@pytest.mark.parametrize('provider', DRIVERS)
def test_where(tmpdir, raster_file, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))
    db.insert({'some': 'a', 'keys': 'third_value'}, str(raster_file))

    data = db.get_datasets()
    assert len(data) == 3

    data = db.get_datasets(where=dict(some='some'))
    assert len(data) == 2

    data = db.get_datasets(where=dict(some='some', keys='value'))
    assert list(data.keys()) == [('some', 'value')]
    assert data[('some', 'value')] == str(raster_file)


@pytest.mark.parametrize('provider', DRIVERS)
def test_lazy_loading(tmpdir, raster_file, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file), compute_metadata=True)
    db.insert(['some', 'other_value'], str(raster_file), compute_metadata=False)

    datasets = db.get_datasets()
    assert len(datasets) == 2

    data1 = db.get_metadata(['some', 'value'])
    data2 = db.get_metadata({'some': 'some', 'keys': 'other_value'})
    assert list(data1.keys()) == list(data2.keys())
    assert all(np.all(data1[k] == data2[k]) for k in data1.keys())


@pytest.mark.parametrize('provider', DRIVERS)
def test_invalid_insertion(tmpdir, raster_file, provider):
    from terracotta import drivers

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('key',)

    db.create(keys)

    def throw(*args, **kwargs):
        raise NotImplementedError()

    db._compute_metadata = throw

    db.insert(['bar'], str(raster_file), compute_metadata=False)

    with pytest.raises(NotImplementedError):
        db.insert(['foo'], str(raster_file), compute_metadata=True)

    datasets = db.get_datasets()

    assert ('bar',) in datasets
    assert ('foo',) not in datasets


@pytest.mark.parametrize('provider', DRIVERS)
def test_invalid_group_insertion(tmpdir, raster_file, provider):
    from terracotta import drivers

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('key',)

    db.create(keys)

    def throw(*args, **kwargs):
        raise NotImplementedError()

    db._compute_metadata = throw

    with db.connect():
        db.insert(['bar'], str(raster_file), compute_metadata=False)

        with pytest.raises(NotImplementedError):
            db.insert(['foo'], str(raster_file), compute_metadata=True)

        datasets = db.get_datasets()

    assert ('bar',) not in datasets
    assert ('foo',) not in datasets


@pytest.mark.parametrize('provider', DRIVERS)
def test_insertion_cache(tmpdir, raster_file, provider):
    from terracotta import drivers

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('key',)

    db.create(keys)
    datasets_before = db.get_datasets()
    db.insert(['foo'], str(raster_file), compute_metadata=False)
    datasets_after = db.get_datasets()

    assert ('foo',) in datasets_after and ('foo',) not in datasets_before


def insertion_worker(key, dbfile, raster_file, provider):
    from terracotta import drivers
    db = drivers.get_driver(str(dbfile), provider=provider)
    db.insert([key], str(raster_file), compute_metadata=True)


@pytest.mark.parametrize('provider', DRIVERS)
def test_multithreaded_insertion(tmpdir, raster_file, provider):
    import functools
    import concurrent.futures
    from terracotta import drivers

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('key',)

    db.create(keys)

    key_vals = [str(i) for i in range(100)]

    worker = functools.partial(insertion_worker, dbfile=dbfile, raster_file=raster_file,
                               provider=provider)

    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        for result in executor.map(worker, key_vals):
            pass

    datasets = db.get_datasets()
    assert all((key,) in datasets for key in key_vals), datasets.keys()

    data1 = db.get_metadata(['77'])
    data2 = db.get_metadata({'key': '99'})
    assert list(data1.keys()) == list(data2.keys())
    assert all(np.all(data1[k] == data2[k]) for k in data1.keys())


@pytest.mark.parametrize('provider', DRIVERS)
def test_multiprocess_insertion(tmpdir, raster_file, provider):
    import functools
    import concurrent.futures
    from terracotta import drivers

    dbfile = str(tmpdir.join('test.sqlite'))
    raster_file = str(raster_file)
    db = drivers.get_driver(dbfile, provider=provider)
    keys = ('key',)

    db.create(keys)

    key_vals = [str(i) for i in range(100)]

    worker = functools.partial(insertion_worker, dbfile=dbfile, raster_file=raster_file,
                               provider=provider)

    with concurrent.futures.ProcessPoolExecutor(4) as executor:
        for result in executor.map(worker, key_vals):
            pass

    datasets = db.get_datasets()
    assert all((key,) in datasets for key in key_vals)

    data1 = db.get_metadata(['77'])
    data2 = db.get_metadata({'key': '99'})
    assert list(data1.keys()) == list(data2.keys())
    assert all(np.all(data1[k] == data2[k]) for k in data1.keys())


@pytest.mark.parametrize('provider', DRIVERS)
def test_insertion_invalid_raster(tmpdir, invalid_raster_file, provider):
    from terracotta import drivers

    dbfile = str(tmpdir.join('test.sqlite'))
    db = drivers.get_driver(dbfile, provider=provider)
    keys = ('key',)

    db.create(keys)

    with pytest.raises(ValueError):
        db.insert(['val'], str(invalid_raster_file))

    datasets = db.get_datasets()
    assert ('val',) not in datasets


@pytest.mark.parametrize('provider', DRIVERS)
def test_raster_retrieval(tmpdir, raster_file, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'other_value'], str(raster_file))

    data1 = db.get_raster_tile(['some', 'value'], tilesize=(256, 256))
    assert data1.shape == (256, 256)

    data2 = db.get_raster_tile(['some', 'other_value'], tilesize=(256, 256))
    assert data2.shape == (256, 256)

    np.testing.assert_array_equal(data1, data2)


@pytest.mark.parametrize('provider', DRIVERS)
def test_raster_duplicate(tmpdir, raster_file, provider):
    from terracotta import drivers
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))
    db.insert(['some', 'value'], str(raster_file))

    assert list(db.get_datasets().keys()) == [('some', 'value')]
