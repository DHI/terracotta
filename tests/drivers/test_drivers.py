import pytest

DRIVERS = ['sqlite', 'mysql']
DRIVER_CLASSES = {
    'sqlite': 'SQLiteDriver',
    'mysql': 'MySQLDriver'
}


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')
    db.create(keys)

    assert db.key_names == keys
    assert db.get_datasets() == {}


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('invalid keyname',)

    with pytest.raises(ValueError):
        db.create(keys)


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid_description(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    with pytest.raises(ValueError):
        db.create(keys, key_descriptions={'unknown_key': 'blah'})


@pytest.mark.parametrize('provider', DRIVERS)
def test_connect_before_create(driver_path, provider):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)

    with pytest.raises(exceptions.InvalidDatabaseError):
        with db.connect():
            pass


@pytest.mark.parametrize('provider', DRIVERS)
def test_repr(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    assert repr(db) == f'{DRIVER_CLASSES[provider]}(\'{driver_path}\')'
