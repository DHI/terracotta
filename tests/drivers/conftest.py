import pytest


@pytest.fixture(params=[('test.sqlite', 'sqlite'), ('root:mysql@localhost:3306', 'mysql')])
def db_params(request, tmpdir, has_mysql):
    if request.param[1] == 'sqlite':
        yield (str(tmpdir.join(request.param[0])), request.param[1])

    else:
        if not has_mysql:
            pytest.skip('MySQL server not running or pymysql not installed')
        yield request.param

        # Cleanup mysql db
        import pymysql  # since has_mysql==True we must have it
        with pymysql.connect('localhost', user='root', password='mysql') as con:
            try:
                con.execute('DROP DATABASE terracotta')
            except pymysql.InternalError:
                # test didn't create a db
                pass
