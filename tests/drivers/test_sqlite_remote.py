"""SQLite-remote driver specific tests.

Tests that apply to all drivers go to test_drivers.py.
"""

import os
import uuid
import tempfile
from pathlib import Path

import pytest

from cachetools import TTLCache

boto3 = pytest.importorskip('boto3')
moto = pytest.importorskip('moto')


@pytest.fixture(autouse=True)
def override_aws_credentials(monkeypatch):
    with monkeypatch.context() as m:
        m.setenv('AWS_ACCESS_KEY_ID', 'FakeKey')
        m.setenv('AWS_SECRET_ACCESS_KEY', 'FakeSecretKey')
        m.setenv('AWS_SESSION_TOKEN', 'FakeSessionToken')
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
            dbfile = Path(tmpdir) / 'tc.sqlite'
            driver = get_driver(dbfile)
            driver.create(keys)

            if datasets:
                for keys, path in datasets.items():
                    driver.insert(keys, path)

            with open(dbfile, 'rb') as f:
                db_bytes = f.read()

        conn = boto3.resource('s3')
        conn.create_bucket(Bucket=bucketname)

        s3 = boto3.client('s3')
        s3.put_object(Bucket=bucketname, Key='tc.sqlite', Body=db_bytes)

        return f's3://{bucketname}/tc.sqlite'

    return _s3_db_factory


@moto.mock_s3
def test_remote_database(s3_db_factory):
    keys = ('some', 'keys')
    dbpath = s3_db_factory(keys)

    from terracotta import get_driver
    driver = get_driver(dbpath)

    assert driver.key_names == keys


def test_invalid_url():
    from terracotta import get_driver
    driver = get_driver('foo', provider='sqlite-remote')
    with pytest.raises(ValueError):
        with driver.connect():
            pass


def test_nonexisting_url():
    from terracotta import get_driver, exceptions
    driver = get_driver('s3://foo/db.sqlite')
    with pytest.raises(exceptions.InvalidDatabaseError):
        with driver.connect():
            pass


@moto.mock_s3
def test_remote_database_cache(s3_db_factory, raster_file, monkeypatch):
    keys = ('some', 'keys')
    dbpath = s3_db_factory(keys)

    from terracotta import get_driver

    driver = get_driver(dbpath)
    with monkeypatch.context() as m:
        # replace TTL cache timer by manual timer
        m.setattr(driver, '_checkdb_cache', TTLCache(maxsize=1, ttl=1, timer=Timer()))
        assert len(driver._checkdb_cache) == 0

        with driver.connect():
            assert driver.key_names == keys
            assert driver.get_datasets() == {}
            modification_date = os.path.getmtime(driver.path)

            s3_db_factory(keys, datasets={('some', 'value'): str(raster_file)})

            # no change yet
            assert driver.get_datasets() == {}
            assert os.path.getmtime(driver.path) == modification_date

        # check if remote db is cached after one tick
        driver._checkdb_cache.timer.tick()
        assert len(driver._checkdb_cache) == 1

        with driver.connect():  # db connection is cached; so still no change
            assert driver.get_datasets() == {}
            assert os.path.getmtime(driver.path) == modification_date

        # TTL cache is invalidated after second tick
        driver._checkdb_cache.timer.tick()
        assert len(driver._checkdb_cache) == 0

        with driver.connect():  # now db is updated on reconnect
            assert list(driver.get_datasets().keys()) == [('some', 'value')]
            assert os.path.getmtime(driver.path) != modification_date


@moto.mock_s3
def test_immutability(s3_db_factory, raster_file):
    keys = ('some', 'keys')
    dbpath = s3_db_factory(keys, datasets={('some', 'value'): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)

    with pytest.raises(NotImplementedError):
        driver.create(keys)

    with pytest.raises(NotImplementedError):
        driver.insert(('some', 'value'), str(raster_file))

    with pytest.raises(NotImplementedError):
        driver.delete(('some', 'value'))


@moto.mock_s3
def test_destructor(s3_db_factory, raster_file, capsys):
    keys = ('some', 'keys')
    dbpath = s3_db_factory(keys, datasets={('some', 'value'): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)
    assert os.path.isfile(driver.path)

    driver.__del__()
    assert not os.path.isfile(driver.path)

    captured = capsys.readouterr()
    assert 'Exception ignored' not in captured.err

    # re-create file to prevent actual destructor from failing
    with open(driver.path, 'w'):
        pass
