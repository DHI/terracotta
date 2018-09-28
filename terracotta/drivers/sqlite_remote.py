"""drivers/sqlite.py

SQLite-backed raster driver. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

from typing import Any, Union
import os
import shutil
import operator
import logging
import urllib.parse as urlparse
from pathlib import Path

from cachetools import cachedmethod, TTLCache

from terracotta import get_settings
from terracotta.drivers.sqlite import SQLiteDriver, convert_exceptions
from terracotta.profile import trace

logger = logging.getLogger(__name__)


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

    def __init__(self, path: Union[str, Path]) -> None:
        """Use given database URL to read metadata."""
        settings = get_settings()

        local_db_path = os.path.join(settings.REMOTE_DB_CACHE_DIR, 's3_db.sqlite')
        os.makedirs(os.path.dirname(local_db_path), exist_ok=True)

        self._remote_path: str = str(path)
        self._checkdb_cache = TTLCache(maxsize=1, ttl=settings.REMOTE_DB_CACHE_TTL)

        super().__init__(local_db_path)

    @cachedmethod(operator.attrgetter('_checkdb_cache'))
    @convert_exceptions('Could not retrieve database from S3')
    @trace('download_db_from_s3')
    def _update_db(self) -> None:
        logger.debug('Remote database cache expired, re-downloading')
        _update_from_s3(self._remote_path, self.path)

    def _check_db(self) -> None:
        self._update_db()
        super()._check_db()

    def create(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def insert(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')
