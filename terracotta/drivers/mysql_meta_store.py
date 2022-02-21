"""drivers/mysql_meta_store.py

MySQL-backed metadata driver. Metadata is stored in a MySQL database.
"""

import functools
from typing import Mapping, Sequence

import sqlalchemy as sqla
from sqlalchemy.dialects.mysql import TEXT, VARCHAR
from terracotta.drivers.relational_meta_store import RelationalMetaStore


class MySQLMetaStore(RelationalMetaStore):
    """A MySQL-backed metadata driver.

    Stores metadata and paths to raster files in MySQL.

    Requires a running MySQL server.

    The MySQL database consists of 4 different tables:

    - ``terracotta``: Metadata about the database itself.
    - ``key_names``: Contains two columns holding all available keys and their description.
    - ``datasets``: Maps key values to physical raster path.
    - ``metadata``: Contains actual metadata as separate columns. Indexed via key values.

    This driver caches key names.
    """
    SQL_DIALECT = 'mysql'
    SQL_DRIVER = 'pymysql'
    SQL_TIMEOUT_KEY = 'connect_timeout'

    _CHARSET = 'utf8mb4'
    SQLA_STRING = functools.partial(VARCHAR, charset=_CHARSET)

    MAX_PRIMARY_KEY_SIZE = 767 // 4  # Max key length for MySQL is at least 767B
    DEFAULT_PORT = 3306

    def __init__(self, mysql_path: str) -> None:
        """Initialize the MySQLDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            mysql_path: URL to running MySQL server, in the form
                ``mysql://username:password@hostname/database``

        """
        super().__init__(f'{mysql_path}?charset={self._CHARSET}')

        self.SQLA_METADATA_TYPE_LOOKUP['text'] = functools.partial(TEXT, charset=self._CHARSET)

        # raise an exception if database name is invalid
        if not self.url.database:
            raise ValueError('database must be specified in MySQL path')
        if '/' in self.url.database.strip('/'):
            raise ValueError('invalid database path')

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        url = cls._parse_path(path)

        path = f'{url.drivername}://{url.host}:{url.port or cls.DEFAULT_PORT}/{url.database}'
        path = path.rstrip('/')
        return path

    def _create_database(self) -> None:
        engine = sqla.create_engine(
            self.url.set(database=''),  # `.set()` returns a copy with changed parameters
            echo=False,
            future=True
        )
        with engine.connect() as connection:
            connection.execute(sqla.text(f'CREATE DATABASE {self.url.database}'))
            connection.commit()

    def _initialize_database(
        self,
        keys: Sequence[str],
        key_descriptions: Mapping[str, str] = None
    ) -> None:
        # total primary key length has an upper limit in MySQL
        self.SQL_KEY_SIZE = self.MAX_PRIMARY_KEY_SIZE // len(keys)
        super()._initialize_database(keys, key_descriptions)
