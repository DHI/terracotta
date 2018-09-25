import pytest

DRIVERS = ['sqlite']


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
def test_connect_before_create(tmpdir, provider):
    from terracotta import drivers, exceptions
    dbfile = tmpdir.join('test.sqlite')
    db = drivers.get_driver(str(dbfile), provider=provider)

    with pytest.raises(exceptions.InvalidDatabaseError):
        with db.connect():
            pass
