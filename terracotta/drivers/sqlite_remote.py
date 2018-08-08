"""drivers/sqlite.py

SQLite-backed raster driver. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

from typing import Any, Union
import os
import urllib.parse as urlparse
from pathlib import Path

from terracotta import get_settings
from terracotta.drivers.sqlite import SQLiteDriver, convert_exceptions


@convert_exceptions('Could not retrieve database from S3')  # type: ignore
def _download_from_s3_if_changed(remote_path: str, local_path: Union[str, Path],
                                 current_hash: str) -> None:
    import boto3
    import botocore

    parsed_remote_path = urlparse.urlparse(remote_path)
    bucket_name, key = parsed_remote_path.netloc, parsed_remote_path.path.strip('/')

    if not parsed_remote_path.scheme == 's3':
        raise ValueError('Expected s3:// URL')

    try:
        s3 = boto3.resource('s3')
        obj = s3.Object(bucket_name, key)
        obj_bytes = obj.get(IfNoneMatch=current_hash)['Body'].read()  # raises if db matches local
        with open(local_path, 'wb') as f:
            f.write(obj_bytes)

    except botocore.exceptions.ClientError as exc:
        assert os.path.isfile(local_path)
        # 304 means hash hasn't changed
        if exc.response['Error']['Code'] != '304':
            raise


class RemoteSQLiteDriver(SQLiteDriver):
    """SQLite-backed raster driver, supports databases stored remotely in an S3 bucket.

    This driver is read-only.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        """Use given database URL to read metadata."""
        settings = get_settings()

        local_db_path = os.path.join(settings.DB_CACHEDIR, 's3_db.sqlite')
        os.makedirs(os.path.dirname(local_db_path), exist_ok=True)

        self._remote_path: str = str(path)

        super(RemoteSQLiteDriver, self).__init__(local_db_path)

    def _check_db(self) -> None:
        _download_from_s3_if_changed(self._remote_path, self.path, self._db_hash)
        super(RemoteSQLiteDriver, self)._check_db()

    def create(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def insert(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')
