"""drivers/sqlite.py

MySQL-backed raster driver. Metadata is stored in a MySQL database, raster data is assumed
to be present on disk.
"""

from typing import (Tuple, Dict, Iterator, Sequence, Union,
                    Mapping, Any, Optional, cast, TypeVar)
from collections import OrderedDict
import contextlib
import re
import json
import urllib.parse as urlparse
from urllib.parse import ParseResult
from pathlib import Path

import numpy as np
import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor  # noqa: F401

from terracotta import get_settings, __version__
from terracotta.drivers.raster_base import RasterDriver
from terracotta.drivers.base import requires_connection
from terracotta import exceptions
from terracotta.profile import trace


T = TypeVar('T')


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    """Convert internal mysql exceptions to our InvalidDatabaseError"""
    from pymysql import OperationalError, InternalError, ProgrammingError
    try:
        yield
    except (OperationalError, InternalError, ProgrammingError) as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


class MySQLDriver(RasterDriver):
    """MySQL-backed raster driver.

    The MySQL database consists of 4 different tables:

    - `terracotta`: Metadata about the database itself.
    - `keys`: Contains a single column holding all available keys.
    - `datasets`: Maps indices to raster file path.
    - `metadata`: Contains actual metadata as separate columns. Indexed via keys.

    """
    MYSQL_MAX_KEY = 191  # Max key length for MySQL is 767, 191 utf8mb4 chars.
    METADATA_COLUMNS: Tuple[Tuple[str, ...], ...] = (
        ('bounds_north', 'REAL'),
        ('bounds_east', 'REAL'),
        ('bounds_south', 'REAL'),
        ('bounds_west', 'REAL'),
        ('convex_hull', 'LONGTEXT'),
        ('nodata', 'REAL'),
        ('valid_percentage', 'REAL'),
        ('min', 'REAL'),
        ('max', 'REAL'),
        ('mean', 'REAL'),
        ('stdev', 'REAL'),
        ('percentiles', 'BLOB'),
        ('metadata', 'LONGTEXT')
    )
    CHARSET: str = 'utf8mb4'

    def __init__(self, path: Union[str, Path]) -> None:
        settings = get_settings()

        self.DB_CONNECTION_TIMEOUT: int = settings.DB_CONNECTION_TIMEOUT

        con_params = urlparse.urlparse(str(path))

        if not con_params.hostname:
            raise ValueError('hostname must be specified in MySQL path')

        self._db_host: str = con_params.hostname
        self._db_user: Optional[str] = con_params.username or None
        self._db_password: Optional[str] = con_params.password
        self._db_port: int = con_params.port or 0
        self._db_name: str = self._parse_db_name(con_params)
        self._connection: Optional[Connection] = None
        self._cursor: Optional[DictCursor] = None

        self._version_checked: bool = False
        self._db_keys: Optional[OrderedDict] = None

        qualified_path = ['mysql://']
        if self._db_user:
            qualified_path.append(f'{self._db_user}')
            if self._db_password:
                qualified_path.append(':[REDACTED]')
            qualified_path.append('@')
        qualified_path.append(self._db_host)
        if con_params.port:
            qualified_path.append(str(self._db_port))
        qualified_path.append(f'/{self._db_name}')

        super().__init__(''.join(qualified_path))

    @staticmethod
    def _parse_db_name(con_params: ParseResult) -> str:
        if not con_params.path:
            raise ValueError('database must be specified in MySQL path')

        path = con_params.path.strip('/')
        if len(path.split('/')) != 1:
            raise ValueError('invalid database path')

        return path

    @requires_connection
    @convert_exceptions('Could not retrieve version from database')
    def _get_db_version(self) -> str:
        """Getter for db_version"""
        cursor = self._get_cursor()
        cursor.execute('SELECT version from terracotta')
        db_row = cast(Dict[str, str], cursor.fetchone())
        return db_row['version']

    def _check_version(self) -> None:
        """Check that the database terracotta version matches ours"""

        # check for version compatibility
        def versiontuple(version_string: str) -> Sequence[str]:
            return version_string.split('.')

        db_version = self._get_db_version()
        current_version = __version__

        if versiontuple(db_version)[:2] != versiontuple(current_version)[:2]:
            raise exceptions.InvalidDatabaseError(
                f'Version conflict: database was created in v{db_version}, '
                f'but this is v{current_version}'
            )

    def _connection_callback(self) -> None:
        if not self._version_checked:
            self._check_version()
            self._version_checked = True

    def _get_key_names(self) -> Tuple[str, ...]:
        """Getter for key_names"""
        return tuple(self.get_keys().keys())

    key_names = cast(Tuple[str], property(_get_key_names))

    def _get_cursor(self) -> DictCursor:
        if self._cursor is None:
            raise RuntimeError('Cursor is None')
        return self._cursor

    @contextlib.contextmanager
    def connect(self, check: bool = True) -> Iterator:
        close = False

        if self._connection is None:
            with convert_exceptions('Unable to connect to database'):
                new_conn = pymysql.connect(
                    host=self._db_host, db=self._db_name, user=self._db_user,
                    password=self._db_password, port=self._db_port,
                    read_timeout=self.DB_CONNECTION_TIMEOUT,
                    write_timeout=self.DB_CONNECTION_TIMEOUT,
                    binary_prefix=True, charset='utf8mb4'
                )

            self._connection = new_conn
            self._cursor = new_conn.cursor(DictCursor)
            if check:
                self._connection_callback()
            close = True

        conn = self._connection
        cursor = self._get_cursor()

        try:
            yield

        except Exception:
            conn.rollback()
            raise

        finally:
            if close:
                conn.commit()
                cursor.close()
                conn.close()
                self._connection = None
                self._cursor = None

    @convert_exceptions('Could not create database')
    def create(self, keys: Sequence[str], key_descriptions: Mapping[str, str] = None) -> None:
        """Initialize database file with empty tables.

        This must be called before opening the first connection.
        """
        if key_descriptions is None:
            key_descriptions = {}
        else:
            key_descriptions = dict(key_descriptions)

        if not all(k in keys for k in key_descriptions.keys()):
            raise ValueError('key description dict contains unknown keys')

        if not all(re.match(r'^\w+$', key) for key in keys):
            raise ValueError('key names can be alphanumeric only')

        for key in keys:
            if key not in key_descriptions:
                key_descriptions[key] = ''

        key_size = self.MYSQL_MAX_KEY // len(keys)
        key_type = f'VARCHAR({key_size})'

        with pymysql.connect(host=self._db_host, user=self._db_user,
                             password=self._db_password, port=self._db_port,
                             read_timeout=self.DB_CONNECTION_TIMEOUT,
                             write_timeout=self.DB_CONNECTION_TIMEOUT,
                             binary_prefix=True, charset='utf8mb4') as con:
            con.execute(f'CREATE DATABASE {self._db_name}')

        with self.connect(check=False):
            cursor = self._get_cursor()
            cursor.execute(f'CREATE TABLE terracotta (version VARCHAR(255)) '
                           f'CHARACTER SET {self.CHARSET}')
            cursor.execute('INSERT INTO terracotta VALUES (%s)', [str(__version__)])

            cursor.execute(f'CREATE TABLE key_names (key_name {key_type}, '
                           f'description VARCHAR(8000)) CHARACTER SET {self.CHARSET}')
            key_rows = [(key, key_descriptions[key]) for key in keys]
            cursor.executemany('INSERT INTO key_names VALUES (%s, %s)', key_rows)

            key_string = ', '.join([f'{key} {key_type}' for key in keys])
            cursor.execute(f'CREATE TABLE datasets ({key_string}, filepath VARCHAR(8000), '
                           f'PRIMARY KEY({", ".join(keys)})) CHARACTER SET {self.CHARSET}')

            column_string = ', '.join(f'{col} {col_type}' for col, col_type
                                      in self.METADATA_COLUMNS)
            cursor.execute(f'CREATE TABLE metadata ({key_string}, {column_string}, '
                           f'PRIMARY KEY ({", ".join(keys)})) CHARACTER SET {self.CHARSET}')

        # invalidate key cache
        self._db_keys = None

    def get_keys(self) -> OrderedDict:
        """Retrieve key names and descriptions from database.

        Caches keys after first call.
        """
        if self._db_keys is None:
            self._db_keys = self._get_keys()
        return self._db_keys

    @requires_connection
    @convert_exceptions('Could not retrieve keys from database')
    def _get_keys(self) -> OrderedDict:
        cursor = self._get_cursor()
        cursor.execute('SELECT * FROM key_names')
        key_rows = cursor.fetchall() or []

        out: OrderedDict = OrderedDict()
        for row in key_rows:
            out[row['key_name']] = row['description']
        return out

    @trace('get_datasets')
    @requires_connection
    @convert_exceptions('Could not retrieve datasets')
    def get_datasets(self, where: Mapping[str, str] = None,
                     page: int = 0, limit: int = 100) -> Dict[Tuple[str, ...], str]:
        """Retrieve keys of datasets matching given pattern"""
        cursor = self._get_cursor()

        # explicitly cast to int to prevent SQL injection
        page_query = f'LIMIT {int(limit)} OFFSET {int(page) * int(limit)}'

        if where is None:
            cursor.execute(f'SELECT * FROM datasets {page_query}')
            rows = cursor.fetchall()
        else:
            if not all(key in self.key_names for key in where.keys()):
                raise exceptions.UnknownKeyError('Encountered unrecognized keys in '
                                                 'where clause')
            where_string = ' AND '.join([f'{key}=%s' for key in where.keys()])
            cursor.execute(f'SELECT * FROM datasets WHERE {where_string}', list(where.values()))
            rows = cursor.fetchall()

        if rows is None:
            rows = tuple()

        def keytuple(row: Dict[str, Any]) -> Tuple[str, ...]:
            return tuple(row[key] for key in self.key_names)

        return {keytuple(row): row['filepath'] for row in rows}

    @staticmethod
    def _encode_data(decoded: Mapping[str, Any]) -> Dict[str, Any]:
        """Transform from internal format to database representation"""
        encoded = {
            'bounds_north': decoded['bounds'][0],
            'bounds_east': decoded['bounds'][1],
            'bounds_south': decoded['bounds'][2],
            'bounds_west': decoded['bounds'][3],
            'convex_hull': json.dumps(decoded['convex_hull']),
            'nodata': decoded['nodata'],
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
            'nodata': encoded['nodata'],
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
        """Retrieve metadata for given keys"""
        keys = tuple(self._key_dict_to_sequence(keys))

        if len(keys) != len(self.key_names):
            raise exceptions.UnknownKeyError('Got wrong number of keys')

        cursor = self._get_cursor()

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

        data_columns, _ = zip(*self.METADATA_COLUMNS)
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
        """Insert a dataset into the database"""
        cursor = self._get_cursor()

        if len(keys) != len(self.key_names):
            raise ValueError(f'Not enough keys (available keys: {self.key_names})')

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
        """Delete a dataset from the database"""
        cursor = self._get_cursor()

        if len(keys) != len(self.key_names):
            raise ValueError(f'Not enough keys (available keys: {self.key_names})')

        keys = self._key_dict_to_sequence(keys)
        key_dict = dict(zip(self.key_names, keys))

        if not self.get_datasets(key_dict):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        where_string = ' AND '.join([f'{key}=%s' for key in self.key_names])
        cursor.execute(f'DELETE FROM datasets WHERE {where_string}', keys)
        cursor.execute(f'DELETE FROM metadata WHERE {where_string}', keys)
