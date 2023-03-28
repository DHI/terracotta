import pytest

TEST_CASES = {
    "{provider}://root@localhost:5000/test": dict(
        username="root", password=None, host="localhost", port=5000, database="test"
    ),
    "root@localhost:5000/test": dict(
        username="root", password=None, host="localhost", port=5000, database="test"
    ),
    "{provider}://root:foo@localhost/test": dict(
        username="root", password="foo", host="localhost", port=None, database="test"
    ),
    "{provider}://localhost/test": dict(
        password=None, host="localhost", port=None, database="test"
    ),
    "localhost/test": dict(password=None, host="localhost", port=None, database="test"),
}

INVALID_TEST_CASES = [
    "http://localhost/test",  # wrong scheme
    "{provider}://localhost",  # no database
    "{provider}://localhost/test/foo/bar",  # path too deep
]


@pytest.mark.parametrize("case", TEST_CASES.keys())
@pytest.mark.parametrize("provider", ("mysql", "postgresql"))
def test_path_parsing(case, provider):
    from terracotta import drivers

    # empty cache
    drivers._DRIVER_CACHE = {}

    db_path = case.format(provider=provider)
    db = drivers.get_driver(db_path, provider=provider)
    for attr in ("username", "password", "host", "port", "database"):
        assert getattr(db.meta_store.url, attr) == TEST_CASES[case].get(attr, None)


@pytest.mark.parametrize("case", INVALID_TEST_CASES)
@pytest.mark.parametrize("provider", ("mysql", "postgresql"))
def test_invalid_paths(case, provider):
    from terracotta import drivers

    db_path = case.format(provider=provider)
    with pytest.raises(ValueError):
        drivers.get_driver(db_path, provider=provider)
