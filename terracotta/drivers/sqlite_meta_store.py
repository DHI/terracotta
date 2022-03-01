"""drivers/sqlite_meta_store.py

SQLite-backed metadata driver. Metadata is stored in an SQLite database.
"""

import os
from pathlib import Path
from typing import Union

from terracotta.drivers.relational_meta_store import RelationalMetaStore


class SQLiteMetaStore(RelationalMetaStore):
    """An SQLite-backed metadata driver.

    Stores metadata and paths to raster files in SQLite.

    This is the simplest Terracotta driver, as it requires no additional infrastructure.
    The SQLite database is simply a file that can e.g. be stored together with the actual
    raster files.

    Note:

        This driver requires the SQLite database to be physically present on the server.
        For remote SQLite databases hosted on S3, use
        :class:`~terracotta.drivers.sqlite_remote.RemoteSQLiteDriver`.

    The SQLite database consists of 4 different tables:

    - ``terracotta``: Metadata about the database itself.
    - ``key_names``: Contains two columns holding all available keys and their description.
    - ``datasets``: Maps key values to physical raster path.
    - ``metadata``: Contains actual metadata as separate columns. Indexed via key values.

    This driver caches key names, but not metadata.

    Warning:

        This driver is not thread-safe. It is not possible to connect to the database
        outside the main thread.

    """
    SQL_DIALECT = 'sqlite'
    SQL_DRIVER = 'pysqlite'
    SQL_KEY_SIZE = 256
    SQL_TIMEOUT_KEY = 'timeout'

    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize the SQLiteDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            path: File path to target SQLite database (may or may not exist yet)

        """
        super().__init__(f'{self.SQL_DIALECT}:///{path}')

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        if path.startswith(f'{cls.SQL_DIALECT}:///'):
            path = path.replace(f'{cls.SQL_DIALECT}:///', '')

        return os.path.normpath(os.path.realpath(path))

    def _create_database(self) -> None:
        """The database is automatically created by the sqlite driver on connection,
        so no need to do anything here
        """
        pass
