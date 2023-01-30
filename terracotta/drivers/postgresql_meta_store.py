"""drivers/postgresql_meta_store.py

PostgreSQL-backed metadata driver. Metadata is stored in a PostgreSQL database.
"""

from typing import Optional, Mapping, Sequence

import sqlalchemy as sqla
from terracotta.drivers.relational_meta_store import RelationalMetaStore


class PostgreSQLMetaStore(RelationalMetaStore):
    """A PostgreSQL-backed metadata driver.

    Stores metadata and paths to raster files in PostgreSQL.

    Requires a running PostgreSQL server.

    The PostgreSQL database consists of 4 different tables:

    - ``terracotta``: Metadata about the database itself.
    - ``key_names``: Contains two columns holding all available keys and their description.
    - ``datasets``: Maps key values to physical raster path.
    - ``metadata``: Contains actual metadata as separate columns. Indexed via key values.

    This driver caches key names.
    """

    SQL_DIALECT = "postgresql"
    SQL_DRIVER = "psycopg2"
    SQL_TIMEOUT_KEY = "connect_timeout"

    MAX_PRIMARY_KEY_SIZE = 2730 // 4  # Max B-tree index size in bytes
    DEFAULT_PORT = 5432
    # Will connect to this db before creatting the 'terracotta' db
    DEFAULT_CONNECT_DB = "postgres"

    def __init__(self, postgresql_path: str) -> None:
        """Initialize the PostgreSQLDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            postgresql_path: URL to running PostgreSQL server, in the form
                ``postgresql://username:password@hostname/database``

        """
        super().__init__(postgresql_path)

        # raise an exception if database name is invalid
        if not self.url.database:
            raise ValueError("database must be specified in PostgreSQL path")
        if "/" in self.url.database.strip("/"):
            raise ValueError("invalid database path")

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        url = cls._parse_path(path)

        path = f"{url.drivername}://{url.host}:{url.port or cls.DEFAULT_PORT}/{url.database}"
        path = path.rstrip("/")
        return path

    def _create_database(self) -> None:
        engine = sqla.create_engine(
            # `.set()` returns a copy with changed parameters
            self.url.set(database=self.DEFAULT_CONNECT_DB),
            echo=False,
            future=True,
            isolation_level="AUTOCOMMIT",
        )
        with engine.connect() as connection:
            connection.execute(sqla.text(f"CREATE DATABASE {self.url.database}"))
            connection.commit()

    def _initialize_database(
        self, keys: Sequence[str], key_descriptions: Optional[Mapping[str, str]] = None
    ) -> None:
        # Enforce max primary key length equal to max B-tree index size
        self.SQL_KEY_SIZE = self.MAX_PRIMARY_KEY_SIZE // len(keys)
        super()._initialize_database(keys, key_descriptions)
