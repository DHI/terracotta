"""drivers/sqlite_remote_meta_store.py

SQLite-backed metadata driver. Metadata is stored in an SQLite database.
"""

import contextlib
import logging
import os
import shutil
import tempfile
import time
import urllib.parse as urlparse
from pathlib import Path
from typing import Any, Iterator, Union

from terracotta import exceptions, get_settings
from terracotta.drivers.sqlite_meta_store import SQLiteMetaStore
from terracotta.profile import trace

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    """Convert internal boto exceptions to our InvalidDatabaseError"""
    import botocore.exceptions
    try:
        yield
    except botocore.exceptions.ClientError as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


def _update_from_s3(remote_path: str, local_path: str) -> None:
    import boto3

    parsed_remote_path = urlparse.urlparse(remote_path)
    bucket_name, key = parsed_remote_path.netloc, parsed_remote_path.path.strip('/')

    if parsed_remote_path.scheme != 's3':
        raise ValueError('Expected s3:// URL')

    s3 = boto3.resource('s3')
    obj = s3.Object(bucket_name, key)
    obj_bytes = obj.get()['Body']

    # copy over existing database; this is somewhat safe since it is read-only
    # NOTE: replace with Connection.backup after switching to Python 3.7
    with open(local_path, 'wb') as f:
        shutil.copyfileobj(obj_bytes, f)


class RemoteSQLiteMetaStore(SQLiteMetaStore):
    """An SQLite-backed metadata driver, where the database file is stored remotely on S3.

    Stores metadata and paths to raster files in SQLite.

    See also:

        :class:`~terracotta.drivers.sqlite.SQLiteDriver` for the local version of this
        driver.

    The SQLite database is simply a file that can be stored e.g. together with the actual
    raster files on S3. Before handling the first request, this driver will download a
    temporary copy of the remote database file. It is thus not feasible for large databases.

    The local database copy will be updated in regular intervals defined by
    :attr:`~terracotta.config.TerracottaSettings.REMOTE_DB_CACHE_TTL`.

    Warning:

        This driver is read-only. Any attempts to use the create, insert, or delete methods
        will throw a NotImplementedError.

    """

    def __init__(self, remote_path: Union[str, Path]) -> None:
        """Initialize the RemoteSQLiteDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            remote_path: S3 URL in the form ``s3://bucket/key`` to remote SQLite database
                (has to exist).

        """
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

        self._local_path = local_db_file.name
        self._remote_path = str(remote_path)
        self._last_updated = -float('inf')

        super().__init__(local_db_file.name)

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        parts = urlparse.urlparse(path)

        if not parts.hostname:
            parts = urlparse.urlparse(f'https://{path}')

        port = parts.port
        if port is None:
            port = 443 if parts.scheme == 'https' else 80

        path = f'{parts.scheme}://{parts.hostname}:{port}{parts.path}'
        path = path.rstrip('/')
        return path

    @convert_exceptions('Could not retrieve database from S3')
    @trace('download_db_from_s3')
    def _update_db(self, remote_path: str, local_path: str) -> None:
        settings = get_settings()

        if self._last_updated < time.time() - settings.REMOTE_DB_CACHE_TTL:
            logger.debug('Remote database cache expired, re-downloading')
            _update_from_s3(remote_path, local_path)
            self._last_updated = time.time()

    def _connection_callback(self) -> None:
        self._update_db(self._remote_path, self._local_path)
        super()._connection_callback()

    def create(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def insert(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError('Remote SQLite databases are read-only')

    def __del__(self) -> None:
        """Clean up temporary database upon exit"""
        self.__rm(self._local_path)
