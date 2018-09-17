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
