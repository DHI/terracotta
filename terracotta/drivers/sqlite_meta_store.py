"""drivers/sqlite_meta_store.py

SQLite-backed raster driver. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

import os
from pathlib import Path
from typing import Union

from terracotta.drivers.relational_meta_store import RelationalMetaStore


class SQLiteMetaStore(RelationalMetaStore):
    """An SQLite-backed raster driver.

    Assumes raster data to be present in separate GDAL-readable files on disk or remotely.
    Stores metadata and paths to raster files in SQLite.

    This is the simplest Terracotta driver, as it requires no additional infrastructure.
    The SQLite database is simply a file that can be stored together with the actual
    raster files.

    Note:

        This driver requires the SQLite database to be physically present on the server.
        For remote SQLite databases hosted on S3, use
        :class:`~terracotta.drivers.sqlite_remote.RemoteSQLiteDriver`.

    The SQLite database consists of 4 different tables:

    - ``terracotta``: Metadata about the database itself.
    - ``keys``: Contains two columns holding all available keys and their description.
    - ``datasets``: Maps key values to physical raster path.
    - ``metadata``: Contains actual metadata as separate columns. Indexed via key values.

    This driver caches raster data and key names, but not metadata.

    Warning:

        This driver is not thread-safe. It is not possible to connect to the database
        outside the main thread.

    """
    SQL_URL_SCHEME = 'sqlite'
    SQL_DRIVER_TYPE = 'pysqlite'
    SQL_KEY_SIZE = 256
    SQL_TIMEOUT_KEY = 'timeout'

    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize the SQLiteDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            path: File path to target SQLite database (may or may not exist yet)

        """
        super().__init__(f'{self.SQL_URL_SCHEME}:///{path}')

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        url = cls._parse_path(path)
        return os.path.normpath(os.path.realpath(url.database))

    def _create_database(self) -> None:
        """The database is automatically created by the sqlite driver on connection,
        so no need to do anything here
        """
        pass
