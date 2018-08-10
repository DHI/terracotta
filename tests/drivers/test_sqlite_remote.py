"""SQLite-remote driver specific tests.

Tests that apply to all drivers go to test_drivers.py.
"""

import os

import pytest

import boto3
from moto import mock_s3


def create_s3_db(keys, tmpdir, datasets=None):
    import uuid
    from terracotta import get_driver

    dbfile = tmpdir / f'{uuid.uuid4()}.sqlite'
    driver = get_driver(dbfile)
    driver.create(keys)

    if datasets:
        for keys, path in datasets.items():
            driver.insert(keys, path)

    with open(dbfile, 'rb') as f:
        db_bytes = f.read()

    conn = boto3.resource('s3')
    conn.create_bucket(Bucket='tctest')

    s3 = boto3.client('s3')
    s3.put_object(Bucket='tctest', Key='tc.sqlite', Body=db_bytes)

    return 's3://tctest/tc.sqlite'


@mock_s3
def test_remote_database(tmpdir):
    keys = ('some', 'keys')
    dbpath = create_s3_db(keys, tmpdir)

    from terracotta import get_driver
    driver = get_driver(dbpath)

    assert driver.available_keys == keys


@mock_s3
def test_remote_database_hash_changed(tmpdir, raster_file):
    keys = ('some', 'keys')
    dbpath = create_s3_db(keys, tmpdir)

    from terracotta import get_driver

    driver = get_driver(dbpath)

    with driver.connect():
        assert driver.available_keys == keys
        assert driver.get_datasets() == {}
        modification_date = os.path.getmtime(driver.path)

        create_s3_db(keys, tmpdir, datasets={('some', 'value'): str(raster_file)})

        # no change yet
        assert driver.get_datasets() == {}
        assert os.path.getmtime(driver.path) == modification_date

    with driver.connect():  # db is updated on reconnect
        assert list(driver.get_datasets().keys()) == [('some', 'value')]
        assert os.path.getmtime(driver.path) != modification_date


@mock_s3
def test_remote_database_hash_unchanged(tmpdir, raster_file):
    keys = ('some', 'keys')
    dbpath = create_s3_db(keys, tmpdir, datasets={('some', 'value'): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)
    assert driver.available_keys == keys
    assert list(driver.get_datasets().keys()) == [('some', 'value')]
    modification_date = os.path.getmtime(driver.path)

    create_s3_db(keys, tmpdir, datasets={('some', 'value'): str(raster_file)})
    assert os.path.getmtime(driver.path) == modification_date
    assert list(driver.get_datasets().keys()) == [('some', 'value')]


@mock_s3
def test_immutability(tmpdir, raster_file):
    keys = ('some', 'keys')
    dbpath = create_s3_db(keys, tmpdir, datasets={('some', 'value'): str(raster_file)})

    from terracotta import get_driver

    driver = get_driver(dbpath)

    with pytest.raises(NotImplementedError):
        driver.create(keys)

    with pytest.raises(NotImplementedError):
        driver.insert(('some', 'value'), str(raster_file))

    with pytest.raises(NotImplementedError):
        driver.delete(('some', 'value'))

