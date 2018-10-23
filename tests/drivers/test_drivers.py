import pytest

DRIVERS = ['sqlite', 'mysql']
DRIVER_CLASSES = {
    'sqlite': 'SQLiteDriver',
    'mysql': 'MySQLDriver'
}


@pytest.fixture()
def driver_path(provider, tmpdir, mysql_server):
    if provider == 'sqlite':
        dbfile = tmpdir.join('test.sqlite')
        yield str(dbfile)

    elif provider == 'mysql':
        try:
            import pymysql
            with pymysql.connect(mysql_server):
                pass
        except (ImportError, pymysql.OperationalError):
            return pytest.skip()
        try:
            yield mysql_server
        finally:
            with pymysql.connect(mysql_server) as conn, conn.cursor() as cursor:
                cursor.execute('DROP TABLE IF EXISTS terracotta')

    else:
        return NotImplementedError()


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keys')
    db.create(keys)

    assert db.key_names == keys
    assert db.get_datasets() == {}


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('invalid key',)

    with pytest.raises(ValueError):
        db.create(keys)


@pytest.mark.parametrize('provider', DRIVERS)
def test_creation_invalid_description(driver_path, provider):
    from terracotta import drivers
    db = drivers.get_driver(driver_path, provider=provider)
    keys = ('some', 'keys')

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
