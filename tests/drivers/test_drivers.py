import pytest

DRIVERS = ['sqlite', 'mysql']
DRIVER_CLASSES = {
    'sqlite': 'SQLiteDriver',
    'mysql': 'MySQLDriver'
}


@pytest.mark.parametrize('provider', DRIVERS)
def test_auto_detect(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path)
    assert db.__class__.__name__ == DRIVER_CLASSES[provider]
    assert drivers.get_driver(driver_path, provider=provider) is db


def test_get_driver_invalid():
    from terracotta import drivers
    with pytest.raises(ValueError) as exc:
        drivers.get_driver('', provider='foo')
    assert 'Unknown database provider' in str(exc.value)


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')
    db.create(keys)

    assert db.key_names == keys
    assert db.get_datasets() == {}


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_descriptions(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')
    key_desc = {'some': 'explanatory text with unicode µóáßð©ßéó'}
    db.create(keys, key_descriptions=key_desc)

    assert db.key_names == keys
    assert db.get_keys()['some'] == key_desc['some']


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid(driver_path, provider):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('invalid keyname',)

    with pytest.raises(exceptions.InvalidKeyError) as exc:
        db.create(keys)

    assert 'must be alphanumeric' in str(exc.value)


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid_description(driver_path, provider):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    with pytest.raises(exceptions.InvalidKeyError) as exc:
        db.create(keys, key_descriptions={'unknown_key': 'blah'})

    assert 'contains unknown keys' in str(exc.value)


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_reserved_names(driver_path, provider):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('page', 'limit')

    with pytest.raises(exceptions.InvalidKeyError) as exc:
        db.create(keys)

    assert 'key names cannot be one of' in str(exc.value)


@pytest.mark.parametrize('provider', DRIVERS)
def test_connect_before_create(driver_path, provider):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)

    with pytest.raises(exceptions.InvalidDatabaseError) as exc:
        with db.connect():
            pass

    assert 'ran driver.create()' in str(exc.value)


@pytest.mark.parametrize('provider', DRIVERS)
def test_repr(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    assert repr(db).startswith(DRIVER_CLASSES[provider])


@pytest.mark.parametrize('provider', DRIVERS)
def test_version_match(driver_path, provider):
    from terracotta import drivers, __version__

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)

    assert __version__ == db.db_version


@pytest.mark.parametrize('provider', DRIVERS)
def test_version_conflict(driver_path, provider, raster_file, monkeypatch):
    from terracotta import drivers, exceptions

    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    db.create(keys)
    db.insert(['some', 'value'], str(raster_file))

    # works
    with db.connect():
        pass

    with monkeypatch.context() as m:
        fake_version = '0.0.0'
        m.setattr(f'{db.__module__}.__version__', fake_version)
        db._version_checked = False

        with pytest.raises(exceptions.InvalidDatabaseError) as exc:
            with db.connect():
                pass

        assert fake_version in str(exc.value)
