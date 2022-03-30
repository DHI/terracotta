"""SQLite-remote driver specific tests.

Tests that apply to all drivers go to test_drivers.py.
"""

import os
import time

import pytest

from terracotta import exceptions

moto = pytest.importorskip('moto')


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


@moto.mock_s3
def test_remote_database(s3_db_factory, mock_aws_env):
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


@moto.mock_s3
def test_nonexisting_url(mock_aws_env):
    from terracotta import exceptions, get_driver
    driver = get_driver('s3://foo/db.sqlite')
    with pytest.raises(exceptions.InvalidDatabaseError):
        with driver.connect():
            pass


@moto.mock_s3
def test_remote_database_cache(s3_db_factory, raster_file, mock_aws_env):
    keys = ('some', 'keys')
    dbpath = s3_db_factory(keys)

    from terracotta import get_driver

    driver = get_driver(dbpath)
    driver.meta_store._last_updated = -float('inf')

    with driver.connect():
        assert driver.key_names == keys
        assert driver.get_datasets() == {}
        modification_date = os.path.getmtime(driver.meta_store._local_path)

        s3_db_factory(keys, datasets={('some', 'value'): str(raster_file)})

        # no change yet
        assert driver.get_datasets() == {}
        assert os.path.getmtime(driver.meta_store._local_path) == modification_date

    # check if remote db is cached correctly
    driver.meta_store._last_updated = time.time()

    with driver.connect():  # db connection is cached; so still no change
        assert driver.get_datasets() == {}
        assert os.path.getmtime(driver.meta_store._local_path) == modification_date

    # invalidate cache
    driver.meta_store._last_updated = -float('inf')

    with driver.connect():  # now db is updated on reconnect
        assert list(driver.get_datasets().keys()) == [('some', 'value')]
        assert os.path.getmtime(driver.meta_store._local_path) != modification_date


@moto.mock_s3
def test_immutability(s3_db_factory, raster_file, mock_aws_env):
    keys = ('some', 'keys')
    dbpath = s3_db_factory(keys, datasets={('some', 'value'): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)

    with pytest.raises(exceptions.DatabaseNotWritableError):
        driver.create(keys)

    with pytest.raises(exceptions.DatabaseNotWritableError):
        driver.insert(('some', 'value'), str(raster_file))

    with pytest.raises(exceptions.DatabaseNotWritableError):
        driver.delete(('some', 'value'))


@moto.mock_s3
def test_destructor(s3_db_factory, raster_file, capsys, mock_aws_env):
    keys = ('some', 'keys')
    dbpath = s3_db_factory(keys, datasets={('some', 'value'): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)
    assert os.path.isfile(driver.meta_store._local_path)

    driver.meta_store.__del__()
    assert not os.path.isfile(driver.meta_store._local_path)

    captured = capsys.readouterr()
    assert 'Exception ignored' not in captured.err

    # re-create file to prevent actual destructor from failing
    with open(driver.meta_store._local_path, 'w'):
        pass
