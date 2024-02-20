"""SQLite-remote driver specific tests.

Tests that apply to all drivers go to test_drivers.py.
"""

import os
import tempfile
import time
import uuid
from pathlib import Path

import pytest

from terracotta import exceptions

boto3 = pytest.importorskip("boto3")
moto = pytest.importorskip("moto")


@pytest.fixture(autouse=True)
def mock_aws_env(monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("AWS_DEFAULT_REGION", "us-east-1")
        m.setenv("AWS_ACCESS_KEY_ID", "FakeKey")
        m.setenv("AWS_SECRET_ACCESS_KEY", "FakeSecretKey")
        m.setenv("AWS_SESSION_TOKEN", "FakeSessionToken")
        yield


class Timer:
    def __init__(self, auto=False):
        self.auto = auto
        self.time = 0

    def __call__(self):
        if self.auto:
            self.time += 1
        return self.time

    def tick(self):
        self.time += 1


@pytest.fixture()
def s3_db_factory(tmpdir):
    bucketname = str(uuid.uuid4())

    def _s3_db_factory(keys, datasets=None):
        from terracotta import get_driver

        with tempfile.TemporaryDirectory() as tmpdir:
            dbfile = Path(tmpdir) / "tc.sqlite"
            driver = get_driver(dbfile)
            driver.create(keys)

            with driver.connect():
                if datasets:
                    for keys, path in datasets.items():
                        driver.insert(keys, path)

            # make sure that the connection is closed
            driver.meta_store.sqla_engine.dispose()

            with open(dbfile, "rb") as f:
                db_bytes = f.read()

        conn = boto3.resource("s3")
        conn.create_bucket(Bucket=bucketname)

        s3 = boto3.client("s3")
        s3.put_object(Bucket=bucketname, Key="tc.sqlite", Body=db_bytes)

        return f"s3://{bucketname}/tc.sqlite"

    return _s3_db_factory


@moto.mock_aws
def test_remote_database(s3_db_factory):
    keys = ("some", "keys")
    dbpath = s3_db_factory(keys)

    from terracotta import get_driver

    driver = get_driver(dbpath)

    assert driver.key_names == keys


def test_invalid_url():
    from terracotta import get_driver

    with pytest.raises(ValueError):
        get_driver("foo", provider="sqlite-remote")


@moto.mock_aws
def test_nonexisting_url():
    from terracotta import exceptions, get_driver

    with pytest.raises(exceptions.InvalidDatabaseError):
        get_driver("s3://foo/db.sqlite")


@moto.mock_aws
def test_remote_database_cache(s3_db_factory, raster_file, monkeypatch):
    keys = ("some", "keys")
    dbpath = s3_db_factory(keys)

    from terracotta import get_driver

    driver = get_driver(dbpath)
    driver.meta_store._last_updated = -float("inf")

    with driver.connect():
        assert driver.key_names == keys
        assert driver.get_datasets() == {}
        modification_date = os.path.getmtime(driver.meta_store._local_path)

        s3_db_factory(keys, datasets={("some", "value"): str(raster_file)})

        # no change yet
        assert driver.get_datasets() == {}
        assert os.path.getmtime(driver.meta_store._local_path) == modification_date

    # check if remote db is cached correctly
    driver.meta_store._last_updated = time.time()

    with driver.connect():  # db connection is cached; so still no change
        assert driver.get_datasets() == {}
        assert os.path.getmtime(driver.meta_store._local_path) == modification_date

    # invalidate cache
    driver.meta_store._last_updated = -float("inf")

    with driver.connect():  # now db is updated on reconnect
        assert list(driver.get_datasets().keys()) == [("some", "value")]
        assert os.path.getmtime(driver.meta_store._local_path) != modification_date


@moto.mock_aws
def test_immutability(s3_db_factory, raster_file):
    keys = ("some", "keys")
    dbpath = s3_db_factory(keys, datasets={("some", "value"): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)

    with pytest.raises(exceptions.DatabaseNotWritableError):
        driver.create(keys)

    with pytest.raises(exceptions.DatabaseNotWritableError):
        driver.insert(("some", "value"), str(raster_file))

    with pytest.raises(exceptions.DatabaseNotWritableError):
        driver.delete(("some", "value"))


@moto.mock_aws
def test_destructor(s3_db_factory, raster_file, capsys):
    keys = ("some", "keys")
    dbpath = s3_db_factory(keys, datasets={("some", "value"): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)
    assert os.path.isfile(driver.meta_store._local_path)

    driver.meta_store.__del__()
    assert not os.path.isfile(driver.meta_store._local_path)

    captured = capsys.readouterr()
    assert "Exception ignored" not in captured.err

    # re-create file to prevent actual destructor from failing
    with open(driver.meta_store._local_path, "w"):
        pass
