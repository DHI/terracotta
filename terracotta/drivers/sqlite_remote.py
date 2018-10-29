"""drivers/sqlite.py

SQLite-backed raster driver. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

from typing import Any, Union, Iterator
import os
import tempfile
import shutil
import operator
import logging
import contextlib
import urllib.parse as urlparse
from pathlib import Path

from cachetools import cachedmethod, TTLCache

from terracotta import get_settings, exceptions
from terracotta.drivers.sqlite import SQLiteDriver
from terracotta.profile import trace

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    """Convert internal sqlite and boto exceptions to our InvalidDatabaseError"""
    import sqlite3
    import botocore.exceptions
    try:
        yield
    except (sqlite3.OperationalError, botocore.exceptions.ClientError) as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


def _update_from_s3(remote_path: str, local_path: str) -> None:
    import boto3

    parsed_remote_path = urlparse.urlparse(remote_path)
    bucket_name, key = parsed_remote_path.netloc, parsed_remote_path.path.strip('/')

    if not parsed_remote_path.scheme == 's3':
        raise ValueError('Expected s3:// URL')

    s3 = boto3.resource('s3')
    obj = s3.Object(bucket_name, key)
    obj_bytes = obj.get()['Body']

    # copy over existing database; this is somewhat safe since it is read-only
    # NOTE: replace with Connection.backup after switching to Python 3.7
    with open(local_path, 'wb') as f:
        shutil.copyfileobj(obj_bytes, f)


class RemoteSQLiteDriver(SQLiteDriver):
    """SQLite-backed raster driver, supports databases stored remotely in an S3 bucket.

    This driver is read-only.
    """
    path: str

    def __init__(self, path: Union[str, Path]) -> None:
        """Use given database URL to read metadata."""
        settings = get_settings()

        self.__rm = os.remove  # keep reference to use in __del__

        os.makedirs(settings.REMOTE_DB_CACHE_DIR, exist_ok=True)
        local_db_file = tempfile.NamedTemporaryFile(
            dir=settings.REMOTE_DB_CACHE_DIR,
            prefix='tc_s3_db_',
            suffix='.sqlite',
            delete=False
        )
        local_db_file.close()

        self._remote_path: str = str(path)
        self._checkdb_cache = TTLCache(maxsize=1, ttl=settings.REMOTE_DB_CACHE_TTL)

        super().__init__(local_db_file.name)

    @cachedmethod(operator.attrgetter('_checkdb_cache'))
    @convert_exceptions('Could not retrieve database from S3')
    @trace('download_db_from_s3')
    def _update_db(self, remote_path: str, local_path: str) -> None:
        logger.debug('Remote database cache expired, re-downloading')
        _update_from_s3(remote_path, local_path)

    def _connection_callback(self, validate: bool = True) -> None:
        self._update_db(self._remote_path, self.path)
        if validate:
            super()._connection_callback()

    def create(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def insert(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def __del__(self) -> None:
        """Clean up temporary database upon exit"""
        rm = self.__rm
        try:
            rm(self.path)
        except AttributeError:
            # object is deleted before self.path is declared
            pass
