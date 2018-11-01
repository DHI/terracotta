import pytest
from urllib.parse import urlparse


def validate_con_info(con_info):
    return (con_info.scheme == 'mysql' and
            con_info.hostname and
            con_info.username and
            con_info.path)


@pytest.fixture()
def driver_path(provider, tmpdir, mysql_server):
    if provider == 'sqlite':
        dbfile = tmpdir.join('test.sqlite')
        yield str(dbfile)

    elif provider == 'mysql':
        if not mysql_server:
            return pytest.skip('mysql_server argument not given')

        con_info = urlparse(mysql_server)
        if not validate_con_info(con_info):
            raise ValueError('invalid value for mysql_server')

        try:
            import pymysql
            with pymysql.connect(con_info.hostname, user=con_info.username,
                                 password=con_info.password) as con:
                pass
        except (ImportError, pymysql.OperationalError) as exc:
            raise RuntimeError('MySQL server not running or pymysql not installed') from exc

        try:
            yield mysql_server

        finally:  # cleanup
            with pymysql.connect(con_info.hostname, user=con_info.username,
                                 password=con_info.password) as con:
                try:
                    con.execute('DROP DATABASE terracotta')
                except pymysql.InternalError:
                    # test didn't create a db
                    pass

    else:
        return NotImplementedError(f'unknown provider {provider}')
