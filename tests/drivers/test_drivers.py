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
