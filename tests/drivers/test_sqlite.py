import pytest


def test_metadata_cache_insertion(tmpdir, raster_file):
    from terracotta import drivers

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider='sqlite')
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))

    metadata_cache = db._metadata_cache

    db.key_names
    assert ('keys', db) in metadata_cache

    db.db_version
    assert ('db_version', db) in metadata_cache

    db.get_datasets()
    assert ('datasets', db, None) in metadata_cache

    db.get_metadata(['some', 'value'])
    assert ('metadata', db, ('some', 'value')) in metadata_cache


def test_metadata_cache_hit(tmpdir, raster_file):
    from terracotta import drivers

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider='sqlite')
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))

    metadata_cache = db._metadata_cache
    db._empty_cache()

    assert len(metadata_cache) == 0

    meta = db.get_metadata(['some', 'value'])

    for _ in range(100):
        assert db.get_metadata(['some', 'value']) == meta

    # contains keys, version, and metadata
    assert len(metadata_cache) == 3


def test_version_match(tmpdir):
    from terracotta import drivers, __version__

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider='sqlite')
    keys = ('some', 'keys')

    db.create(keys)

    assert __version__ == db.db_version


def test_version_conflict(tmpdir, raster_file, monkeypatch):
    from terracotta import drivers, exceptions

    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider='sqlite')
    keys = ('some', 'keys')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))

    # works
    with db.connect():
        pass

    with monkeypatch.context() as m:
        fake_version = '0.0.0'
        m.setattr('terracotta.drivers.sqlite.__version__', fake_version)

        # works
        with db.connect(check=False):
            pass

        # fails
        with pytest.raises(exceptions.InvalidDatabaseError) as exc:
            with db.connect(check=True):
                pass

            assert fake_version in str(exc.value)
