import os.path

import pytest


DRIVER_CLASSES = {
    'sqlite': 'SQLiteDriver',
    'mysql': 'MySQLDriver'
}


def test_creation(db_params):
    from terracotta import drivers
    path, provider = db_params
    db = drivers.get_driver(path, provider=provider)
    keys = ('some', 'keynames')
    db.create(keys)

    assert db.key_names == keys
    assert db.get_datasets() == {}
    if provider == 'sqlite':
        assert os.path.isfile(path)


def test_creation_invalid(db_params):
    from terracotta import drivers, exceptions
    path, provider = db_params
    db = drivers.get_driver(path, provider=provider)
    keys = ('invalid keyname',)

    if provider == 'sqlite':
        with pytest.raises(ValueError):
            db.create(keys)
    elif provider == 'mysql':
        with pytest.raises(exceptions.InvalidDatabaseError):
            db.create(keys)


def test_creation_invalid_description(db_params):
    from terracotta import drivers
    path, provider = db_params
    db = drivers.get_driver(path, provider=provider)
    keys = ('some', 'keynames')

    with pytest.raises(ValueError):
        db.create(keys, key_descriptions={'unknown_key': 'blah'})


def test_connect_before_create(db_params):
    from terracotta import drivers, exceptions
    path, provider = db_params
    db = drivers.get_driver(path, provider=provider)

    with pytest.raises(exceptions.InvalidDatabaseError):
        with db.connect():
            pass


def test_repr(db_params):
    from terracotta import drivers
    path, provider = db_params
    db = drivers.get_driver(path, provider=provider)
    assert repr(db) == f'{DRIVER_CLASSES[provider]}(\'{path}\')'
