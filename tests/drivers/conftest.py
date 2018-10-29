import pytest


@pytest.fixture()
def driver_path(provider, tmpdir, mysql_server):
    if provider == 'sqlite':
        dbfile = tmpdir.join('test.sqlite')
        yield str(dbfile)

    elif provider == 'mysql':
        if not mysql_server:
            return pytest.skip('mysql_server argument not given')

        from terracotta.drivers import parse_connection
        con_info = parse_connection(mysql_server)

        if not con_info:
            raise ValueError('invalid value for mysql_server')

        try:
            import pymysql
            with pymysql.connect(con_info.host, user=con_info.user, password=con_info.password):
                pass
        except (ImportError, pymysql.OperationalError) as exc:
            raise RuntimeError('MySQL server not running or pymysql not installed') from exc

        try:
            yield mysql_server

        finally:  # cleanup
            with pymysql.connect(con_info.host, user=con_info.user,
                                 password=con_info.password) as con:
                con.execute('DROP DATABASE IF EXISTS terracotta')

    else:
        return NotImplementedError(f'unknown provider {provider}')
