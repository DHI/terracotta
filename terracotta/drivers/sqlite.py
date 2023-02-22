"""drivers/sqlite.py

SQLite-backed raster driver. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

from typing import Any, List, Sequence, Mapping, Tuple, Union, Iterator, Dict, cast
import os
import contextlib
from contextlib import AbstractContextManager
import json
import re
import sqlite3
from sqlite3 import Connection
from pathlib import Path
from collections import OrderedDict

import numpy as np

from terracotta import get_settings, exceptions, __version__
from terracotta.profile import trace
from terracotta.drivers.base import requires_connection
from terracotta.drivers.raster_base import RasterDriver

_ERROR_ON_CONNECT = (
    'Could not connect to database. Make sure that the given path points '
    'to a valid Terracotta database, and that you ran driver.create().'
)


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    """Convert internal sqlite exceptions to our InvalidDatabaseError"""
    try:
        yield
    except sqlite3.OperationalError as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


class SQLiteDriver(RasterDriver):
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

    This driver caches raster data, but not metadata.

    Warning:

        This driver is not thread-safe. It is not possible to connect to the database
        outside the main thread.

    """
    _KEY_TYPE: str = 'VARCHAR[256]'
    _METADATA_COLUMNS: Tuple[Tuple[str, ...], ...] = (
        ('bounds_north', 'REAL'),
        ('bounds_east', 'REAL'),
        ('bounds_south', 'REAL'),
        ('bounds_west', 'REAL'),
        ('convex_hull', 'VARCHAR[max]'),
        ('valid_percentage', 'REAL'),
        ('min', 'REAL'),
        ('max', 'REAL'),
        ('mean', 'REAL'),
        ('stdev', 'REAL'),
        ('percentiles', 'BLOB'),
        ('metadata', 'VARCHAR[max]')
    )

    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize the SQLiteDriver.

        This should not be called directly, use :func:`~terracotta.get_driver` instead.

        Arguments:

            path: File path to target SQLite database (may or may not exist yet)

        """
        path = str(path)

        settings = get_settings()
        self.DB_CONNECTION_TIMEOUT: int = settings.DB_CONNECTION_TIMEOUT
        self.LAZY_LOADING_MAX_SHAPE: Tuple[int, int] = settings.LAZY_LOADING_MAX_SHAPE

        self._connection: Connection
        self._connected = False

        super().__init__(os.path.realpath(path))

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        return os.path.normpath(os.path.realpath(path))

    def connect(self) -> AbstractContextManager:
        return self._connect(check=True)

    @contextlib.contextmanager
    def _connect(self, check: bool = True) -> Iterator:
        try:
            close = False
            if not self._connected:
                with convert_exceptions(_ERROR_ON_CONNECT):
                    self._connection = sqlite3.connect(
                        self.path, timeout=self.DB_CONNECTION_TIMEOUT
                    )
                self._connection.row_factory = sqlite3.Row
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
                self._connection.commit()
                self._connection.close()

    @requires_connection
    @convert_exceptions(_ERROR_ON_CONNECT)
    def _get_db_version(self) -> str:
        """Terracotta version used to create the database"""
        conn = self._connection
        db_row = conn.execute('SELECT version from terracotta').fetchone()
        return db_row['version']

    db_version = cast(str, property(_get_db_version))

    def _connection_callback(self) -> None:
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
        """Names of all keys defined by the database"""
        return tuple(self.get_keys().keys())

    key_names = cast(Tuple[str], property(_get_key_names))

    @convert_exceptions('Could not create database')
    def create(self, keys: Sequence[str], key_descriptions: Mapping[str, str] = None) -> None:
        """Create and initialize database with empty tables.

        This must be called before opening the first connection. Tables must not exist already.

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

        with self._connect(check=False):
            conn = self._connection
            conn.execute('CREATE TABLE terracotta (version VARCHAR[255])')
            conn.execute('INSERT INTO terracotta VALUES (?)', [str(__version__)])

            conn.execute(f'CREATE TABLE keys (key {self._KEY_TYPE}, description VARCHAR[max])')
            key_rows = [(key, key_descriptions[key]) for key in keys]
            conn.executemany('INSERT INTO keys VALUES (?, ?)', key_rows)

            key_string = ', '.join([f'{key} {self._KEY_TYPE}' for key in keys])
            conn.execute(f'CREATE TABLE datasets ({key_string}, filepath VARCHAR[8000], '
                         f'PRIMARY KEY({", ".join(keys)}))')

            column_string = ', '.join(f'{col} {col_type}' for col, col_type
                                      in self._METADATA_COLUMNS)
            conn.execute(f'CREATE TABLE metadata ({key_string}, {column_string}, '
                         f'PRIMARY KEY ({", ".join(keys)}))')

    @requires_connection
    @convert_exceptions('Could not retrieve keys from database')
    def get_keys(self) -> OrderedDict:
        conn = self._connection
        key_rows = conn.execute('SELECT * FROM keys')

        out: OrderedDict = OrderedDict()
        for row in key_rows:
            out[row['key']] = row['description']
        return out

    @trace('get_datasets')
    @requires_connection
    @convert_exceptions('Could not retrieve datasets')
    def get_datasets(self, where: Mapping[str, Union[str, List[str]]] = None,
                     page: int = 0, limit: int = None) -> Dict[Tuple[str, ...], str]:
        conn = self._connection

        if limit is not None:
            # explicitly cast to int to prevent SQL injection
            page_fragment = f'LIMIT {int(limit)} OFFSET {int(page) * int(limit)}'
        else:
            page_fragment = ''

        # sort by keys to ensure deterministic results
        order_fragment = f'ORDER BY {", ".join(self.key_names)}'

        if where is None:
            rows = conn.execute(f'SELECT * FROM datasets {order_fragment} {page_fragment}')
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
                conditions.append(' OR '.join([f'{key}=?'] * len(value)))
            where_fragment = ' AND '.join([f'({condition})' for condition in conditions])
            rows = conn.execute(
                f'SELECT * FROM datasets WHERE {where_fragment} {order_fragment} {page_fragment}',
                values
            )

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
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        conn = self._connection

        where_string = ' AND '.join([f'{key}=?' for key in self.key_names])
        row = conn.execute(f'SELECT * FROM metadata WHERE {where_string}', keys).fetchone()

        if not row:  # support lazy loading
            filepath = self.get_datasets(dict(zip(self.key_names, keys)), page=0, limit=1)
            if not filepath:
                raise exceptions.DatasetNotFoundError(f'No dataset found for given keys {keys}')

            # compute metadata and try again
            metadata = self.compute_metadata(filepath[keys], max_shape=self.LAZY_LOADING_MAX_SHAPE)
            self.insert(keys, filepath[keys], metadata=metadata)
            row = conn.execute(f'SELECT * FROM metadata WHERE {where_string}', keys).fetchone()

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
        conn = self._connection

        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        if override_path is None:
            override_path = filepath

        keys = self._key_dict_to_sequence(keys)
        template_string = ', '.join(['?'] * (len(keys) + 1))
        conn.execute(f'INSERT OR REPLACE INTO datasets VALUES ({template_string})',
                     [*keys, override_path])

        if metadata is None and not skip_metadata:
            metadata = self.compute_metadata(filepath)

        if metadata is not None:
            encoded_data = self._encode_data(metadata)
            row_keys, row_values = zip(*encoded_data.items())
            template_string = ', '.join(['?'] * (len(keys) + len(row_values)))
            conn.execute(f'INSERT OR REPLACE INTO metadata ({", ".join(self.key_names)}, '
                         f'{", ".join(row_keys)}) VALUES ({template_string})', [*keys, *row_values])

    @trace('delete')
    @requires_connection
    @convert_exceptions('Could not write to database')
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        conn = self._connection

        if len(keys) != len(self.key_names):
            raise exceptions.InvalidKeyError(
                f'Got wrong number of keys (available keys: {self.key_names})'
            )

        keys = self._key_dict_to_sequence(keys)
        key_dict = dict(zip(self.key_names, keys))

        if not self.get_datasets(key_dict):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        where_string = ' AND '.join([f'{key}=?' for key in self.key_names])
        conn.execute(f'DELETE FROM datasets WHERE {where_string}', keys)
        conn.execute(f'DELETE FROM metadata WHERE {where_string}', keys)
