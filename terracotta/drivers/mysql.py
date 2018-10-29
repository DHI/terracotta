"""drivers/sqlite.py

MySQL-backed raster driver. Metadata is stored in a MySQL database, raster data is assumed
to be present on disk.
"""

from typing import (Tuple, Dict, Iterator, Callable, Sequence, Union,
                    Mapping, Any, Optional, cast, TYPE_CHECKING)
from collections import OrderedDict
import contextlib
from datetime import datetime
import functools
import re
import json

import numpy as np

from terracotta import get_settings, __version__
from terracotta.drivers.base import T
from terracotta.drivers.raster_base import RasterDriver
from terracotta import exceptions
from terracotta.profile import trace

if TYPE_CHECKING:
    from pymysql.connections import Connection, Cursor
    from pymysql.cursors import DictCursor  # noqa: F401


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    """Convert internal mysql exceptions to our InvalidDatabaseError"""
    from pymysql import OperationalError, InternalError, ProgrammingError
    try:
        yield
    except (OperationalError, InternalError, ProgrammingError) as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


def requires_cursor(fun: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(fun)
    def inner(self: 'MySQLDriver', *args: Any, **kwargs: Any) -> T:
        with self.cursor():
            return fun(self, *args, **kwargs)
    return inner


class MySQLDriver(RasterDriver):
    """MySQL-backed raster driver.

    Thread-safe by opening a single connection per thread.

    The MySQL database consists of 4 different tables:

    - `terracotta`: Metadata about the database itself.
    - `keys`: Contains a single column holding all available keys.
    - `datasets`: Maps indices to raster file path.
    - `metadata`: Contains actual metadata as separate columns. Indexed via keys.

    """
    KEY_TYPE: str = 'VARCHAR(255)'
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

    def __init__(self, host: str = 'localhost', user: str = None,
                 password: str = None, port: int = 0) -> None:
        settings = get_settings()

        self.DB_CONNECTION_TIMEOUT: int = settings.DB_CONNECTION_TIMEOUT

        self._db_host: str = host
        self._db_user: Optional[str] = user
        self._db_password: Optional[str] = password
        self._db_port: int = port
        self._db_last_update: datetime = datetime.min
        self._connection: Optional[Connection] = None
        self._cursor: Optional[Cursor] = None

        super().__init__(f'{user}:{password}@{host}:{port}')

    @requires_cursor
    @convert_exceptions('Could not retrieve version from database')
    def _get_db_version(self) -> str:
        """Getter for db_version"""
        cursor = cast('DictCursor', self._cursor)
        cursor.execute('SELECT version from terracotta')
        db_row = cast(Dict[str, str], cursor.fetchone())
        return db_row['version']

    db_version = cast(str, property(_get_db_version))

    @requires_cursor
    def _after_connection(self) -> None:
        """Called after opening a new connection"""

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

    def _get_key_names(self) -> Tuple[str, ...]:
        """Getter for key_names"""
        return tuple(self.get_keys().keys())

    key_names = cast(Tuple[str], property(_get_key_names))

    @contextlib.contextmanager
    def connect(self, check: bool = True, nodb: bool = False) -> 'Iterator[Connection]':
        import pymysql

        close = False

        if nodb:
            db = None
        else:
            db = 'terracotta'

        if self._connection is None:
            with convert_exceptions('Unable to connect to database'):
                new_conn = pymysql.connect(
                    host=self._db_host, db=db, user=self._db_user, password=self._db_password,
                    port=self._db_port, read_timeout=self.DB_CONNECTION_TIMEOUT,
                    write_timeout=self.DB_CONNECTION_TIMEOUT, binary_prefix=True,
                    charset='utf8mb4'
                )

            self._connection = new_conn
            if not nodb and check:
                self._after_connection()
            close = True

        conn = self._connection

        try:
            yield conn

        except Exception:
            conn.rollback()
            raise

        finally:
            if close:
                conn.commit()
                conn.close()
                self._connection = None

    @contextlib.contextmanager
    def cursor(self, check: bool = True, nodb: bool = False) -> 'Iterator[Cursor]':
        from pymysql.cursors import DictCursor  # noqa: F811

        close = False

        with self.connect(nodb=nodb):
            if self._cursor is None:
                self._cursor = cast('Connection', self._connection).cursor(DictCursor)
                close = True
            cursor = cast('Cursor', self._cursor)

            try:
                yield cursor

            finally:
                if close:
                    cursor.close()
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

        with self.cursor(nodb=True) as cursor:
            cursor.execute(f'CREATE DATABASE terracotta')
            cursor.execute(f'USE terracotta')
            cursor.execute('CREATE TABLE terracotta (version VARCHAR(255))')
            cursor.execute('INSERT INTO terracotta VALUES (%s)', [str(__version__)])

            cursor.execute(f'CREATE TABLE key_names (key_name {self.KEY_TYPE}, '
                           'description VARCHAR(8000))')
            key_rows = [(key, key_descriptions[key]) for key in keys]
            cursor.executemany('INSERT INTO key_names VALUES (%s, %s)', key_rows)

            key_string = ', '.join([f'{key} {self.KEY_TYPE}' for key in keys])
            cursor.execute(f'CREATE TABLE datasets ({key_string}, filepath VARCHAR(8000), '
                           f'PRIMARY KEY({", ".join(keys)}))')

            column_string = ', '.join(f'{col} {col_type}' for col, col_type
                                      in self.METADATA_COLUMNS)
            cursor.execute(f'CREATE TABLE metadata ({key_string}, {column_string}, '
                           f'PRIMARY KEY ({", ".join(keys)}))')

    @requires_cursor
    @convert_exceptions('Could not retrieve keys from database')
    def get_keys(self) -> OrderedDict:
        """Retrieve key names and descriptions from database"""
        cursor = cast('DictCursor', self._cursor)
        cursor.execute('SELECT * FROM key_names')
        key_rows = cursor.fetchall() or []

        out: OrderedDict = OrderedDict()
        for row in key_rows:
            out[row['key_name']] = row['description']
        return out

    @trace('get_datasets')
    @requires_cursor
    @convert_exceptions('Could not retrieve datasets')
    def get_datasets(self, where: Mapping[str, str] = None) -> Dict[Tuple[str, ...], str]:
        """Retrieve keys of datasets matching given pattern"""
        cursor = cast('DictCursor', self._cursor)

        if where is None:
            cursor.execute(f'SELECT * FROM datasets')
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
    @requires_cursor
    @convert_exceptions('Could not retrieve metadata')
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        """Retrieve metadata for given keys"""
        keys = tuple(self._key_dict_to_sequence(keys))

        if len(keys) != len(self.key_names):
            raise exceptions.UnknownKeyError('Got wrong number of keys')

        cursor = cast('DictCursor', self._cursor)

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
    @requires_cursor
    @convert_exceptions('Could not write to database')
    def insert(self,
               keys: Union[Sequence[str], Mapping[str, str]],
               filepath: str, *,
               metadata: Mapping[str, Any] = None,
               skip_metadata: bool = False,
               override_path: str = None) -> None:
        """Insert a dataset into the database"""
        cursor = cast('Cursor', self._cursor)

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
    @requires_cursor
    @convert_exceptions('Could not write to database')
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        """Delete a dataset from the database"""
        cursor = cast('Cursor', self._cursor)

        if len(keys) != len(self.key_names):
            raise ValueError(f'Not enough keys (available keys: {self.key_names})')

        keys = self._key_dict_to_sequence(keys)
        key_dict = dict(zip(self.key_names, keys))

        if not self.get_datasets(key_dict):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        where_string = ' AND '.join([f'{key}=%s' for key in self.key_names])
        cursor.execute(f'DELETE FROM datasets WHERE {where_string}', keys)
        cursor.execute(f'DELETE FROM metadata WHERE {where_string}', keys)
