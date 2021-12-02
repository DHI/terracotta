import pytest

TEST_CASES = {
    'mysql://root@localhost:5000/test': dict(
        username='root', password=None, hostname='localhost', port=5000, path='/test'
    ),
    'root@localhost:5000/test': dict(
        username='root', password=None, hostname='localhost', port=5000, path='/test'
    ),
    'mysql://root:foo@localhost/test': dict(
        username='root', password='foo', hostname='localhost', port=None, path='/test'
    ),
    'mysql://localhost/test': dict(
        password=None, hostname='localhost', port=None, path='/test'
    ),
    'localhost/test': dict(
        password=None, hostname='localhost', port=None, path='/test'
    )
}

INVALID_TEST_CASES = [
    'http://localhost/test',  # wrong scheme
    'mysql://localhost',  # no database
    'mysql://localhost/test/foo/bar'  # path too deep
]


@pytest.mark.parametrize('case', TEST_CASES.keys())
def test_path_parsing(case):
    from terracotta import drivers
    # empty cache
    drivers._DRIVER_CACHE = {}

    db = drivers.get_driver(case, provider='mysql')
    db_args = db._CONNECTION_PARAMETERS
    print(db_args)
    for attr in ('username', 'password', 'hostname', 'port', 'path'):
        print(attr)
        assert getattr(db_args, attr) == TEST_CASES[case].get(attr, None)


@pytest.mark.parametrize('case', INVALID_TEST_CASES)
def test_invalid_paths(case):
    from terracotta import drivers

    with pytest.raises(ValueError):
        drivers.get_driver(case, provider='mysql')
