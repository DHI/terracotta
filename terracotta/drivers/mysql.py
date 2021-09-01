"""drivers/sqlite.py

MySQL-backed raster driver. Metadata is stored in a MySQL database, raster data is assumed
to be present on disk.
"""

from typing import (List, Tuple, Dict, Iterator, Sequence, Union,
                    Mapping, Any, Optional, cast, TypeVar)
from collections import OrderedDict
import contextlib
from contextlib import AbstractContextManager
import re
import json
import urllib.parse as urlparse
from urllib.parse import ParseResult

import numpy as np
import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from terracotta import get_settings, __version__
from terracotta.drivers.raster_base import RasterDriver
from terracotta.drivers.base import requires_connection
from terracotta import exceptions
from terracotta.profile import trace


T = TypeVar('T')

_ERROR_ON_CONNECT = (
    'Could not connect to database. Make sure that the given path points '
    'to a valid Terracotta database, and that you ran driver.create().'
)

DEFAULT_PORT = 3306


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    """Convert internal mysql exceptions to our InvalidDatabaseError"""
    from pymysql import OperationalError, InternalError, ProgrammingError
    try:
        yield
    except (OperationalError, InternalError, ProgrammingError) as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


class MySQLCredentials:
    __slots__ = ('host', 'port', 'db', '_user', '_password')

    def __init__(self,
                 host: str,
                 port: int,
                 db: str,
                 user: Optional[str] = None,
                 password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self._user = user
        self._password = password

    @property
    def user(self) -> Optional[str]:
        return self._user or get_settings().MYSQL_USER

    @property
    def password(self) -> str:
        pw = self._password or get_settings().MYSQL_PASSWORD

        if pw is None:
            pw = ''

        return pw


class MySQLDriver(RasterDriver):
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
    _MAX_PRIMARY_KEY_LENGTH = 767 // 4  # Max key length for MySQL is at least 767B
    _METADATA_COLUMNS: Tuple[Tuple[str, ...], ...] = (
        ('bounds_north', 'REAL'),
        ('bounds_east', 'REAL'),
        ('bounds_south', 'REAL'),
        ('bounds_west', 'REAL'),
        ('convex_hull', 'LONGTEXT'),
        ('valid_percentage', 'REAL'),
        ('min', 'REAL'),
        ('max', 'REAL'),
        ('mean', 'REAL'),
        ('stdev', 'REAL'),
        ('percentiles', 'BLOB'),
        ('metadata', 'LONGTEXT')
    )
    _CHARSET: str = 'utf8mb4'

    def __init__(self, mysql_path: str) -> None:
        """Initialize the MySQLDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            mysql_path: URL to running MySQL server, in the form
                ``mysql://username:password@hostname/database``

        """
        settings = get_settings()

        self.DB_CONNECTION_TIMEOUT: int = settings.DB_CONNECTION_TIMEOUT

        con_params = urlparse.urlparse(mysql_path)

        if not con_params.hostname:
            con_params = urlparse.urlparse(f'mysql://{mysql_path}')

        assert con_params.hostname is not None

        if con_params.scheme != 'mysql':
            raise ValueError(f'unsupported URL scheme "{con_params.scheme}"')

        self._db_args = MySQLCredentials(
            host=con_params.hostname,
            user=con_params.username,
            password=con_params.password,
            port=con_params.port or DEFAULT_PORT,
            db=self._parse_db_name(con_params)
        )

        self._connection: Connection
        self._cursor: DictCursor
        self._connected = False

        self._version_checked: bool = False
        self._db_keys: Optional[OrderedDict] = None

        # use normalized path to make sure username and password don't leak into __repr__
        qualified_path = self._normalize_path(mysql_path)
        super().__init__(qualified_path)

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        parts = urlparse.urlparse(path)

        if not parts.hostname:
            parts = urlparse.urlparse(f'mysql://{path}')

        path = f'{parts.scheme}://{parts.hostname}:{parts.port or DEFAULT_PORT}{parts.path}'
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

    @requires_connection
    @convert_exceptions(_ERROR_ON_CONNECT)
    def _get_db_version(self) -> str:
        """Terracotta version used to create the database"""
        cursor = self._cursor
        cursor.execute('SELECT version from terracotta')
        db_row = cast(Dict[str, str], cursor.fetchone())
        return db_row['version']

    db_version = cast(str, property(_get_db_version))

    def _connection_callback(self) -> None:
        if not self._version_checked:
            # check for version compatibility
            def versiontuple(version_string: str) -> Sequence[str]:
                return version_string.split('.')

            db_version = self.db_version
            current_version = __version__

            if versiontuple(db_version)[:2] != versiontuple(current_version)[:2]:
                raise exceptions.InvalidDatabaseError(
                    f'Version conflict: database was created in v{db_version}, '
                    f'but this is v{current_version}'
                )
            self._version_checked = True

    def _get_key_names(self) -> Tuple[str, ...]:
        """Names of all keys defined by the database"""
        return tuple(self.get_keys().keys())

    key_names = cast(Tuple[str], property(_get_key_names))

    def connect(self) -> AbstractContextManager:
        return self._connect(check=True)

    @contextlib.contextmanager
    def _connect(self, check: bool = True) -> Iterator:
        close = False
        try:
            if not self._connected:
                with convert_exceptions(_ERROR_ON_CONNECT):
                    self._connection = pymysql.connect(
                        host=self._db_args.host, user=self._db_args.user, db=self._db_args.db,
                        password=self._db_args.password, port=self._db_args.port,
                        read_timeout=self.DB_CONNECTION_TIMEOUT,
                        write_timeout=self.DB_CONNECTION_TIMEOUT,
                        binary_prefix=True, charset='utf8mb4'
                    )
                self._cursor = self._connection.cursor(DictCursor)
                self._connected = close = True

                if check:
                    self._connection_callback()

            try:
                yield
            except Exception:
                self._connection.rollback()
                raise

        finally:
            if close:
                self._connected = False
                self._cursor.close()
                self._connection.commit()
                self._connection.close()

    @convert_exceptions('Could not create database')
    def create(self, keys: Sequence[str], key_descriptions: Mapping[str, str] = None) -> None:
        """Create and initialize database with empty tables.

        This must be called before opening the first connection. The MySQL database must not
        exist already.

        Arguments:

            keys: Key names to use throughout the Terracotta database.
            key_descriptions: Optional (but recommended) full-text description for some keys,
                in the form of ``{key_name: description}``.

        """
        if key_descriptions is None:
            key_descriptions = {}
        else:
            key_descriptions = dict(key_descriptions)

        if not all(k in keys for k in key_descriptions.keys()):
            raise exceptions.InvalidKeyError('key description dict contains unknown keys')

        if not all(re.match(r'^\w+$', key) for key in keys):
            raise exceptions.InvalidKeyError('key names must be alphanumeric')

        if any(key in self._RESERVED_KEYS for key in keys):
            raise exceptions.InvalidKeyError(f'key names cannot be one of {self._RESERVED_KEYS!s}')

        for key in keys:
            if key not in key_descriptions:
                key_descriptions[key] = ''

        # total primary key length has an upper limit in MySQL
        key_size = self._MAX_PRIMARY_KEY_LENGTH // len(keys)
        key_type = f'VARCHAR({key_size})'

        connection = pymysql.connect(
            host=self._db_args.host, user=self._db_args.user,
            password=self._db_args.password, port=self._db_args.port,
            read_timeout=self.DB_CONNECTION_TIMEOUT,
            write_timeout=self.DB_CONNECTION_TIMEOUT,
            binary_prefix=True, charset='utf8mb4'
        )

        with connection, connection.cursor() as cursor:  # type: ignore
            cursor.execute(f'CREATE DATABASE {self._db_args.db}')

        with self._connect(check=False):
            cursor = self._cursor
            cursor.execute(f'CREATE TABLE terracotta (version VARCHAR(255)) '
                           f'CHARACTER SET {self._CHARSET}')
            cursor.execute('INSERT INTO terracotta VALUES (%s)', [str(__version__)])

            cursor.execute(f'CREATE TABLE key_names (key_name {key_type}, '
                           f'description VARCHAR(8000)) CHARACTER SET {self._CHARSET}')
            key_rows = [(key, key_descriptions[key]) for key in keys]
            cursor.executemany('INSERT INTO key_names VALUES (%s, %s)', key_rows)

            key_string = ', '.join([f'{key} {key_type}' for key in keys])
            cursor.execute(f'CREATE TABLE datasets ({key_string}, filepath VARCHAR(8000), '
                           f'PRIMARY KEY({", ".join(keys)})) CHARACTER SET {self._CHARSET}')

            column_string = ', '.join(f'{col} {col_type}' for col, col_type
                                      in self._METADATA_COLUMNS)
            cursor.execute(f'CREATE TABLE metadata ({key_string}, {column_string}, '
                           f'PRIMARY KEY ({", ".join(keys)})) CHARACTER SET {self._CHARSET}')

        # invalidate key cache
        self._db_keys = None

    def get_keys(self) -> OrderedDict:
        if self._db_keys is None:
            self._db_keys = self._get_keys()
        return self._db_keys

    @requires_connection
    @convert_exceptions('Could not retrieve keys from database')
    def _get_keys(self) -> OrderedDict:
        out: OrderedDict = OrderedDict()

        cursor = self._cursor
        cursor.execute('SELECT * FROM key_names')
        key_rows = cursor.fetchall() or ()

        for row in key_rows:
            out[row['key_name']] = row['description']

        return out

    @trace('get_datasets')
    @requires_connection
    @convert_exceptions('Could not retrieve datasets')
    def get_datasets(self, where: Mapping[str, Union[str, List[str]]] = None,
                     page: int = 0, limit: int = None) -> Dict[Tuple[str, ...], str]:
        cursor = self._cursor

        if limit is not None:
            # explicitly cast to int to prevent SQL injection
            page_fragment = f'LIMIT {int(limit)} OFFSET {int(page) * int(limit)}'
        else:
            page_fragment = ''

        # sort by keys to ensure deterministic results
        order_fragment = f'ORDER BY {", ".join(self.key_names)}'

        if where is None:
            cursor.execute(f'SELECT * FROM datasets {order_fragment} {page_fragment}')
        else:
            if not all(key in self.key_names for key in where.keys()):
                raise exceptions.InvalidKeyError('Encountered unrecognized keys in '
                                                 'where clause')
            conditions = []
            values = []
            for key, value in where.items():
                if isinstance(value, str):
                    value = [value]
                values.extend(value)
                conditions.append(' OR '.join([f'{key}=%s'] * len(value)))
            where_fragment = ' AND '.join([f'({condition})' for condition in conditions])
            cursor.execute(
                f'SELECT * FROM datasets WHERE {where_fragment} {order_fragment} {page_fragment}',
                values
            )

        def keytuple(row: Dict[str, Any]) -> Tuple[str, ...]:
            return tuple(row[key] for key in self.key_names)

        datasets = {}
        for row in cursor:
            datasets[keytuple(row)] = row['filepath']

        return datasets

    @staticmethod
    def _encode_data(decoded: Mapping[str, Any]) -> Dict[str, Any]:
        """Transform from internal format to database representation"""
        encoded = {
            'bounds_north': decoded['bounds'][0],
            'bounds_east': decoded['bounds'][1],
            'bounds_south': decoded['bounds'][2],
            'bounds_west': decoded['bounds'][3],
            'convex_hull': json.dumps(decoded['convex_hull']),
            'valid_percentage': decoded['valid_percentage'],
            'min': decoded['range'][0],
            'max': decoded['range'][1],
            'mean': decoded['mean'],
            'stdev': decoded['stdev'],
            'percentiles': np.array(decoded['percentiles'], dtype='float32').tobytes(),
            'metadata': json.dumps(decoded['metadata'])
        }
        return encoded

    @staticmethod
    def _decode_data(encoded: Mapping[str, Any]) -> Dict[str, Any]:
        """Transform from database format to internal representation"""
        decoded = {
            'bounds': tuple([encoded[f'bounds_{d}'] for d in ('north', 'east', 'south', 'west')]),
            'convex_hull': json.loads(encoded['convex_hull']),
            'valid_percentage': encoded['valid_percentage'],
            'range': (encoded['min'], encoded['max']),
            'mean': encoded['mean'],
            'stdev': encoded['stdev'],
            'percentiles': np.frombuffer(encoded['percentiles'], dtype='float32').tolist(),
            'metadata': json.loads(encoded['metadata'])
        }
        return decoded

    @trace('get_metadata')
    @requires_connection
    @convert_exceptions('Could not retrieve metadata')
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        keys = tuple(self._key_dict_to_sequence(keys))

        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError('Got wrong number of keys')

        cursor = self._cursor

        where_string = ' AND '.join([f'{key}=%s' for key in self.key_names])
        cursor.execute(f'SELECT * FROM metadata WHERE {where_string}', keys)
        row = cursor.fetchone()

        if not row:  # support lazy loading
            filepath = self.get_datasets(dict(zip(self.key_names, keys)))
            if not filepath:
                raise exceptions.DatasetNotFoundError(f'No dataset found for given keys {keys}')
            assert len(filepath) == 1

            # compute metadata and try again
            self.insert(keys, filepath[keys], skip_metadata=False)
            cursor.execute(f'SELECT * FROM metadata WHERE {where_string}', keys)
            row = cursor.fetchone()

        assert row

        data_columns, _ = zip(*self._METADATA_COLUMNS)
        encoded_data = {col: row[col] for col in self.key_names + data_columns}
        return self._decode_data(encoded_data)

    @trace('insert')
    @requires_connection
    @convert_exceptions('Could not write to database')
    def insert(self,
               keys: Union[Sequence[str], Mapping[str, str]],
               filepath: str, *,
               metadata: Mapping[str, Any] = None,
               skip_metadata: bool = False,
               override_path: str = None) -> None:
        cursor = self._cursor

        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        if override_path is None:
            override_path = filepath

        keys = self._key_dict_to_sequence(keys)
        template_string = ', '.join(['%s'] * (len(keys) + 1))
        cursor.execute(f'REPLACE INTO datasets VALUES ({template_string})',
                       [*keys, override_path])

        if metadata is None and not skip_metadata:
            metadata = self.compute_metadata(filepath)

        if metadata is not None:
            encoded_data = self._encode_data(metadata)
            row_keys, row_values = zip(*encoded_data.items())
            template_string = ', '.join(['%s'] * (len(keys) + len(row_values)))
            cursor.execute(f'REPLACE INTO metadata ({", ".join(self.key_names)}, '
                           f'{", ".join(row_keys)}) VALUES ({template_string})',
                           [*keys, *row_values])

    @trace('delete')
    @requires_connection
    @convert_exceptions('Could not write to database')
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        cursor = self._cursor

        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        keys = self._key_dict_to_sequence(keys)
        key_dict = dict(zip(self.key_names, keys))

        if not self.get_datasets(key_dict):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        where_string = ' AND '.join([f'{key}=%s' for key in self.key_names])
        cursor.execute(f'DELETE FROM datasets WHERE {where_string}', keys)
        cursor.execute(f'DELETE FROM metadata WHERE {where_string}', keys)
