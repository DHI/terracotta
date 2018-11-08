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
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('invalid keyname',)

    with pytest.raises(exceptions.InvalidKeyError):
        db.create(keys)


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid_description(driver_path, provider):
    from terracotta import drivers, exceptions
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keynames')

    with pytest.raises(exceptions.InvalidKeyError):
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

        # works
        with db.connect(check=False):
            pass

        # fails
        with pytest.raises(exceptions.InvalidDatabaseError) as exc:
            with db.connect(check=True):
                pass

            assert fake_version in str(exc.value)
