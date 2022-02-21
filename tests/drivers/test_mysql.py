import pytest

TEST_CASES = {
    'mysql://root@localhost:5000/test': dict(
        username='root', password=None, host='localhost', port=5000, database='test'
    ),
    'root@localhost:5000/test': dict(
        username='root', password=None, host='localhost', port=5000, database='test'
    ),
    'mysql://root:foo@localhost/test': dict(
        username='root', password='foo', host='localhost', port=None, database='test'
    ),
    'mysql://localhost/test': dict(
        password=None, host='localhost', port=None, database='test'
    ),
    'localhost/test': dict(
        password=None, host='localhost', port=None, database='test'
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
    for attr in ('username', 'password', 'host', 'port', 'database'):
        assert getattr(db.meta_store.url, attr) == TEST_CASES[case].get(attr, None)


@pytest.mark.parametrize('case', INVALID_TEST_CASES)
def test_invalid_paths(case):
    from terracotta import drivers

    with pytest.raises(ValueError):
        drivers.get_driver(case, provider='mysql')
