"""drivers/sqlite.py

SQLite-backed raster driver. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

from typing import Any, Sequence, Mapping, Tuple, Union, Iterator, Dict, Callable, cast
import sys
import os
import operator
import functools
import contextlib
import json
import re
import sqlite3
from sqlite3 import Connection
from threading import get_ident
from pathlib import Path
from hashlib import md5

from cachetools import LFUCache, cachedmethod
import cachetools.keys
import numpy as np

from terracotta import get_settings, exceptions, __version__
from terracotta.profile import trace
from terracotta.drivers.base import requires_connection
from terracotta.drivers.raster_base import RasterDriver


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    """Convert internal sqlite exceptions to our InvalidDatabaseError"""
    try:
        yield
    except sqlite3.OperationalError as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


def shared_cachedmethod(key: str) -> Callable[..., Callable[..., Any]]:
    """Decorator that supports a shared metadata cache"""
    return cachedmethod(operator.attrgetter('_metadata_cache'),
                        key=functools.partial(cachetools.keys.hashkey, key))


class SQLiteDriver(RasterDriver):
    """SQLite-backed raster driver.

    Thread-safe by opening a single connection per thread.

    The SQLite database consists of 4 different tables:

    - `terracotta`: Metadata about the database itself.
    - `keys`: Contains a single column holding all available keys.
    - `datasets`: Maps indices to raster file path.
    - `metadata`: Contains actual metadata as separate columns. Indexed via keys.

    This driver caches both raster and metadata (in separate caches).

    """
    KEY_TYPE: str = 'VARCHAR[256]'
    METADATA_COLUMNS: Tuple[Tuple[str, ...], ...] = (
        ('bounds_north', 'REAL'),
        ('bounds_east', 'REAL'),
        ('bounds_south', 'REAL'),
        ('bounds_west', 'REAL'),
        ('convex_hull', 'VARCHAR[max]'),
        ('nodata', 'REAL'),
        ('valid_percentage', 'REAL'),
        ('min', 'REAL'),
        ('max', 'REAL'),
        ('mean', 'REAL'),
        ('stdev', 'REAL'),
        ('percentiles', 'BLOB'),
        ('metadata', 'VARCHAR[max]')
    )

    def __init__(self, path: Union[str, Path]) -> None:
        """Use given database path to read and store metadata."""
        settings = get_settings()

        self.DB_CONNECTION_TIMEOUT: int = settings.DB_CONNECTION_TIMEOUT

        self.path: str = str(path)

        self._connection_pool: Dict[int, Connection] = {}
        self._metadata_cache: LFUCache = LFUCache(
            settings.METADATA_CACHE_SIZE, getsizeof=sys.getsizeof
        )

        self._db_hash: str = ''
        if os.path.isfile(self.path):
            self._db_hash = self._compute_hash(self.path)

        super().__init__(path)

    def _get_connection(self) -> Connection:
        """Convenience method to retrieve the correct connection for the current thread."""
        thread_id = get_ident()
        if thread_id not in self._connection_pool:
            raise RuntimeError('No open connection for current thread')
        return self._connection_pool[thread_id]

    @contextlib.contextmanager
    def connect(self, check: bool = True) -> Iterator:
        thread_id = get_ident()
        close = False

        if thread_id not in self._connection_pool:
            with convert_exceptions('Unable to connect to database'):
                new_conn = sqlite3.connect(self.path, timeout=self.DB_CONNECTION_TIMEOUT)
            new_conn.row_factory = sqlite3.Row
            self._connection_pool[thread_id] = new_conn
            if check:
                self._check_db()
            close = True

        conn = self._get_connection()

        try:
            yield conn

        except Exception:
            conn.rollback()
            raise

        finally:
            if close:
                conn.commit()
                conn.close()
                self._connection_pool.pop(thread_id)

    @shared_cachedmethod('db_version')
    @requires_connection
    @convert_exceptions('Could not retrieve version from database')
    def _get_db_version(self) -> str:
        """Getter for db_version"""
        conn = self._get_connection()
        db_row = conn.execute('SELECT version from terracotta').fetchone()
        return db_row['version']

    db_version = cast(str, property(_get_db_version))

    def _check_db(self) -> None:
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

        # invalidate cache if db has changed since last connection
        new_hash = self._compute_hash(self.path)
        if self._db_hash != new_hash:
            self._empty_cache()
            self._db_hash = new_hash

    @staticmethod
    def _compute_hash(path: Union[str, Path]) -> str:
        m = md5()
        with open(path, 'rb') as f:
            m.update(f.read())
        return m.hexdigest()

    def _empty_cache(self) -> None:
        self._metadata_cache.clear()

    @shared_cachedmethod('keys')
    @requires_connection
    @convert_exceptions('Could not retrieve keys from database')
    def _get_available_keys(self) -> Tuple[str, ...]:
        """Getter for available_keys"""
        conn = self._get_connection()
        key_rows = conn.execute('SELECT keys FROM keys').fetchall()
        return tuple(row['keys'] for row in key_rows)

    available_keys = cast(Tuple[str], property(_get_available_keys))

    @convert_exceptions('Could not create database')
    def create(self, keys: Sequence[str]) -> None:
        """Initialize database file with empty tables. 
        
        This must be called before the first call to `connect()`.
        """
        if not all(re.match(r'\w+', key) for key in keys):
            raise ValueError('keys can be alphanumeric only')

        with self.connect(check=False) as conn:
            conn.execute('CREATE TABLE terracotta (version VARCHAR[255])')
            conn.execute('INSERT INTO terracotta VALUES (?)', [str(__version__)])

            conn.execute(f'CREATE TABLE keys (keys {self.KEY_TYPE})')
            conn.executemany('INSERT INTO keys VALUES (?)', [(key,) for key in keys])

            key_string = ', '.join([f'{key} {self.KEY_TYPE}' for key in keys])
            conn.execute(f'CREATE TABLE datasets ({key_string}, filepath VARCHAR[8000], '
                         f'PRIMARY KEY({", ".join(keys)}))')

            column_string = ', '.join(f'{col} {col_type}' for col, col_type
                                      in self.METADATA_COLUMNS)
            conn.execute(f'CREATE TABLE metadata ({key_string}, {column_string}, '
                         f'PRIMARY KEY ({", ".join(keys)}))')

    @shared_cachedmethod('datasets')
    def _get_datasets(self, where: Tuple[Tuple[str, str], ...]) -> Dict[Tuple[str, ...], str]:
        """Cache-backed version of get_datasets"""
        conn = self._get_connection()

        if where is None:
            rows = conn.execute(f'SELECT * FROM datasets')
        else:
            where_keys, where_values = zip(*where)
            if not all(key in self.available_keys for key in where_keys):
                raise exceptions.UnknownKeyError('Encountered unrecognized keys in '
                                                 'where clause')
            where_string = ' AND '.join([f'{key}=?' for key in where_keys])
            rows = conn.execute(f'SELECT * FROM datasets WHERE {where_string}', where_values)

        def keytuple(row: sqlite3.Row) -> Tuple[str, ...]:
            return tuple(row[key] for key in self.available_keys)

        return {keytuple(row): row['filepath'] for row in rows}

    @trace('get_datasets')
    @requires_connection
    @convert_exceptions('Could not retrieve datasets')
    def get_datasets(self, where: Mapping[str, str] = None) -> Dict[Tuple[str, ...], str]:
        """Retrieve keys of datasets matching given pattern"""
        # make sure arguments are hashable
        if where is None:
            return self._get_datasets(None)

        return self._get_datasets(tuple(where.items()))

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

    @shared_cachedmethod('metadata')
    def _get_metadata(self, keys: Tuple[str]) -> Dict[str, Any]:
        """Cache-backed version of get_metadata"""
        if len(keys) != len(self.available_keys):
            raise exceptions.UnknownKeyError('Got wrong number of keys')

        conn = self._get_connection()

        where_string = ' AND '.join([f'{key}=?' for key in self.available_keys])
        row = conn.execute(f'SELECT * FROM metadata WHERE {where_string}', keys).fetchone()

        if not row:  # support lazy loading
            filepath = self._get_datasets(tuple(zip(self.available_keys, keys)))
            if not filepath:
                raise exceptions.DatasetNotFoundError(f'No dataset found for given keys {keys}')
            assert len(filepath) == 1

            # compute metadata and try again
            self.insert(keys, filepath[keys], skip_metadata=False)
            row = conn.execute(f'SELECT * FROM metadata WHERE {where_string}', keys).fetchone()

        assert row

        data_columns, _ = zip(*self.METADATA_COLUMNS)
        encoded_data = {col: row[col] for col in self.available_keys + data_columns}
        return self._decode_data(encoded_data)

    @trace('get_metadata')
    @requires_connection
    @convert_exceptions('Could not retrieve metadata')
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        """Retrieve metadata for given keys"""
        # make sure arguments are hashable
        keys = tuple(self._key_dict_to_sequence(keys))
        return self._get_metadata(keys)

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
        conn = self._get_connection()

        if len(keys) != len(self.available_keys):
            print(keys, self.available_keys)
            raise ValueError('Not enough keys')

        if override_path is None:
            override_path = filepath

        keys = list(self._key_dict_to_sequence(keys))
        template_string = ', '.join(['?'] * (len(keys) + 1))
        conn.execute(f'INSERT OR REPLACE INTO datasets VALUES ({template_string})',
                     [*keys, override_path])

        if metadata is None and not skip_metadata:
            metadata = self.compute_metadata(filepath)

        if metadata is not None:
            encoded_data = self._encode_data(metadata)
            row_keys, row_values = zip(*encoded_data.items())
            template_string = ', '.join(['?'] * (len(keys) + len(row_values)))
            conn.execute(f'INSERT OR REPLACE INTO metadata ({", ".join(self.available_keys)}, '
                         f'{", ".join(row_keys)}) VALUES ({template_string})', [*keys, *row_values])

    @trace('delete')
    @requires_connection
    @convert_exceptions('Could not write to database')
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        """Delete a dataset from the database"""
        conn = self._get_connection()

        if len(keys) != len(self.available_keys):
            raise ValueError('Not enough keys')

        keys = list(self._key_dict_to_sequence(keys))
        key_dict = dict(zip(self.available_keys, keys))

        if not self.get_datasets(key_dict):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        where_string = ' AND '.join([f'{key}=?' for key in self.available_keys])
        conn.execute(f'DELETE FROM datasets WHERE {where_string}', keys)
        conn.execute(f'DELETE FROM metadata WHERE {where_string}', keys)
