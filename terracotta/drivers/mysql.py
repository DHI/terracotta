"""drivers/mysql.py

MySQL-backed raster driver. Metadata is stored in a MySQL database, raster data is assumed
to be present on disk.
"""

from urllib.parse import ParseResult

import sqlalchemy as sqla
from terracotta.drivers.common import RelationalDriver


class MySQLDriver(RelationalDriver):
    """A MySQL-backed raster driver.

    Assumes raster data to be present in separate GDAL-readable files on disk or remotely.
    Stores metadata and paths to raster files in MySQL.

    Requires a running MySQL server.

    The MySQL database consists of 4 different tables:

    - ``terracotta``: Metadata about the database itself.
    - ``key_names``: Contains two columns holding all available keys and their description.
    - ``datasets``: Maps key values to physical raster path.
    - ``metadata``: Contains actual metadata as separate columns. Indexed via key values.

    This driver caches raster data and key names, but not metadata.
    """
    SQL_DATABASE_SCHEME = 'mysql'
    SQL_DRIVER_TYPE = 'pymysql'
    SQL_KEY_SIZE = 50
    SQL_TIMEOUT_KEY = 'connect_timeout'

    DEFAULT_PORT = 3306

    def __init__(self, mysql_path: str) -> None:
        """Initialize the MySQLDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            mysql_path: URL to running MySQL server, in the form
                ``mysql://username:password@hostname/database``

        """
        super().__init__(mysql_path)
        self._parse_db_name(self._CONNECTION_PARAMETERS)  # To enforce path is parsable

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        parts = cls._parse_connection_string(path)

        path = f'{parts.scheme}://{parts.hostname}:{parts.port or cls.DEFAULT_PORT}{parts.path}'
        path = path.rstrip('/')
        return path

    @staticmethod
    def _parse_db_name(con_params: ParseResult) -> str:
        if not con_params.path:
            raise ValueError('database must be specified in MySQL path')

        path = con_params.path.strip('/')
        if '/' in path:
            raise ValueError('invalid database path')

        return path

    def _create_database(self) -> None:
        engine = sqla.create_engine(
            f'{self._CONNECTION_PARAMETERS.scheme}+{self.SQL_DRIVER_TYPE}://'
            f'{self._CONNECTION_PARAMETERS.netloc}',
            echo=True,
            future=True
        )
        with engine.connect() as connection:
            db_name = self._parse_db_name(self._CONNECTION_PARAMETERS)
            connection.execute(sqla.text(f'CREATE DATABASE {db_name}'))
            connection.commit()
