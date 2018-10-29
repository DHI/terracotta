import pytest


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
