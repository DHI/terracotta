"""SQLite-remote driver specific tests.

Tests that apply to all drivers go to test_drivers.py.
"""

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
            print(f'inserting {keys}')
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
    assert driver.available_keys == keys
    assert driver.get_datasets() == {}
    create_s3_db(keys, tmpdir, datasets={('some', 'value'): str(raster_file)})
    print('real driver: ', driver)
    assert list(driver.get_datasets().keys()) == [('some', 'value')]
