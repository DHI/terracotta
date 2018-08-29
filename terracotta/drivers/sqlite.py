"""drivers/sqlite.py

SQLite-backed raster driver. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

from typing import Any, Sequence, Mapping, Tuple, Union, Callable, Iterator, Dict
import sys
import os
import operator
import contextlib
import functools
import json
import re
from threading import get_ident
from pathlib import Path
import sqlite3
from sqlite3 import Connection
from hashlib import md5

from cachetools import LFUCache, cachedmethod
import numpy as np

from terracotta.drivers.base import requires_connection
from terracotta.drivers.raster_base import RasterDriver
from terracotta import get_settings, exceptions


def memoize(fun: Callable) -> Callable:
    cache: Dict[Tuple[Any, ...], Any] = {}

    @functools.wraps(fun)
    def inner(*args: Any) -> Any:
        if args not in cache:
            cache[args] = fun(*args)
        return cache[args]

    return inner


@contextlib.contextmanager
def convert_exceptions(msg: str) -> Iterator:
    try:
        yield
    except sqlite3.OperationalError as exc:
        raise exceptions.InvalidDatabaseError(msg) from exc


class SQLiteDriver(RasterDriver):
    """SQLite-backed raster driver.

    Thread-safe by opening a single connection per thread.

    Data is stored in 3 different tables:

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
        ('nodata', 'REAL'),
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

        super(SQLiteDriver, self).__init__(path)

    @staticmethod
    def _compute_hash(path: Union[str, Path]) -> str:
        m = md5()
        with open(path, 'rb') as f:
            m.update(f.read())
        return m.hexdigest()

    def _empty_cache(self) -> None:
        settings = get_settings()
        self._metadata_cache = LFUCache(
            settings.METADATA_CACHE_SIZE, getsizeof=sys.getsizeof
        )

    # TODO: use marshmallow schema instead
    @staticmethod
    def _encode_data(decoded: Mapping[str, Any]) -> Dict[str, Any]:
        """Transform from internal format to database representation"""
        encoded = {
            'bounds_north': decoded['bounds'][0],
            'bounds_east': decoded['bounds'][1],
            'bounds_south': decoded['bounds'][2],
            'bounds_west': decoded['bounds'][3],
            'nodata': decoded['nodata'],
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
            'nodata': encoded['nodata'],
            'range': (encoded['min'], encoded['max']),
            'mean': encoded['mean'],
            'stdev': encoded['stdev'],
            'percentiles': np.frombuffer(encoded['percentiles'], dtype='float32').tolist(),
            'metadata': json.loads(encoded['metadata'])
        }
        return decoded

    def get_connection(self) -> Connection:
        """Convenience method to retrieve the correct connection for the current thread."""
        thread_id = get_ident()
        if thread_id not in self._connection_pool:
            raise RuntimeError('No open connection for current thread')
        return self._connection_pool[thread_id]

    @contextlib.contextmanager
    def connect(self) -> Iterator:
        thread_id = get_ident()
        if thread_id not in self._connection_pool:
            self._check_db()
            with convert_exceptions('Unable to connect to database'):
                new_conn = sqlite3.connect(self.path, timeout=self.DB_CONNECTION_TIMEOUT)
            self._connection_pool[thread_id] = new_conn
            close = True
        else:
            close = False

        conn = self.get_connection()

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

    def _check_db(self) -> None:
        """Called when opening a new connection"""
        if not os.path.isfile(self.path):
            return

        new_hash = self._compute_hash(self.path)
        if self._db_hash != new_hash:
            self._empty_cache()
            self._db_hash = new_hash

    @memoize
    @convert_exceptions('Could not retrieve keys from database')
    @requires_connection
    def _get_available_keys(self) -> Tuple[str, ...]:
        """Caching getter for available_keys. Assumes keys do not change during runtime."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM keys')
        return tuple(row[0] for row in c)

    available_keys = property(_get_available_keys)  # type: ignore

    @convert_exceptions('Could not create tables')
    @requires_connection
    def create(self, keys: Sequence[str], drop_if_exists: bool = False) -> None:
        if not all(re.match(r'\w+', key) for key in keys):
            raise ValueError('keys can be alphanumeric only')

        conn = self.get_connection()
        c = conn.cursor()

        if drop_if_exists:
            c.execute('DROP TABLE IF EXISTS keys')
        c.execute(f'CREATE TABLE keys (keys {self.KEY_TYPE})')
        c.executemany('INSERT INTO keys VALUES (?)', [(key,) for key in keys])

        if drop_if_exists:
            c.execute('DROP TABLE IF EXISTS datasets')
        key_string = ', '.join([f'{key} {self.KEY_TYPE}' for key in keys])
        c.execute(f'CREATE TABLE datasets ({key_string}, filepath VARCHAR[8000], '
                  f'PRIMARY KEY({", ".join(keys)}))')

        if drop_if_exists:
            c.execute('DROP TABLE IF EXISTS metadata')
        column_string = ', '.join(f'{col} {col_type}' for col, col_type
                                  in self.METADATA_COLUMNS)
        c.execute(f'CREATE TABLE metadata ({key_string}, {column_string}, '
                  f'PRIMARY KEY ({", ".join(keys)}))')

    @cachedmethod(operator.attrgetter('_metadata_cache'))
    def _get_datasets(self,
                      where: Tuple[Tuple[str], Tuple[str]] = None) -> Dict[Tuple[str, ...], str]:
        """Cache-backed version of get_datasets"""
        conn = self.get_connection()
        c = conn.cursor()

        if where is None:
            c.execute(f'SELECT * FROM datasets')

        else:
            where_keys, where_values = where
            if not all(key in self.available_keys for key in where_keys):
                raise exceptions.UnknownKeyError('Encountered unrecognized keys in '
                                                 'where clause')
            where_string = ' AND '.join([f'{key}=?' for key in where_keys])
            c.execute(f'SELECT * FROM datasets WHERE {where_string}', where_values)

        num_keys = len(self.available_keys)
        return {tuple(row[:num_keys]): row[-1] for row in c}

    @convert_exceptions('Could not retrieve datasets')
    @requires_connection
    def get_datasets(self, where: Mapping[str, str] = None) -> Dict[Tuple[str, ...], str]:
        where_ = where and (tuple(where.keys()), tuple(where.values()))
        return self._get_datasets(where_)

    @cachedmethod(operator.attrgetter('_metadata_cache'))
    def _get_metadata(self, keys: Tuple[str]) -> Dict[str, Any]:
        """Cache-backed version of get_metadata"""
        if len(keys) != len(self.available_keys):
            raise exceptions.UnknownKeyError('Got wrong number of keys')

        conn = self.get_connection()
        c = conn.cursor()

        where_string = ' AND '.join([f'{key}=?' for key in self.available_keys])
        c.execute(f'SELECT * FROM metadata WHERE {where_string}', keys)

        rows = list(c)
        if not rows:  # support lazy loading
            filepath = self._get_datasets((self.available_keys, keys))
            if not filepath:
                raise exceptions.DatasetNotFoundError(f'No dataset found for given keys {keys}')
            assert len(filepath) == 1
            # compute metadata and try again
            self.insert(keys, filepath[keys], skip_metadata=False)
            c.execute(f'SELECT * FROM metadata WHERE {where_string}', keys)
            rows = list(c)

        data_columns, _ = zip(*self.METADATA_COLUMNS)
        encoded_data = [dict(zip(self.available_keys + data_columns, row)) for row in rows]
        assert len(encoded_data) == 1
        return self._decode_data(encoded_data[0])

    @convert_exceptions('Could not retrieve metadata')
    @requires_connection
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        keys = tuple(self._key_dict_to_sequence(keys))
        return self._get_metadata(keys)

    @convert_exceptions('Could not write to database')
    @requires_connection
    def insert(self,
               keys: Union[Sequence[str], Mapping[str, str]],
               filepath: str, *,
               metadata: Mapping[str, Any] = None,
               skip_metadata: bool = False,
               override_path: str = None) -> None:
        conn = self.get_connection()
        c = conn.cursor()

        if len(keys) != len(self.available_keys):
            raise ValueError('Not enough keys')

        if override_path is None:
            override_path = filepath

        keys = list(self._key_dict_to_sequence(keys))
        template_string = ', '.join(['?'] * (len(keys) + 1))
        c.execute(f'INSERT OR REPLACE INTO datasets VALUES ({template_string})',
                  keys + [override_path])

        if metadata is None and not skip_metadata:
            metadata = self.compute_metadata(filepath)

        if metadata is not None:
            encoded_data = self._encode_data(metadata)
            row_keys, row_values = zip(*encoded_data.items())
            template_string = ', '.join(['?'] * (len(keys) + len(row_values)))
            c.execute(f'INSERT OR REPLACE INTO metadata ({", ".join(self.available_keys)}, '
                      f'{", ".join(row_keys)}) VALUES ({template_string})', keys + list(row_values))

    @convert_exceptions('Could not write to database')
    @requires_connection
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        conn = self.get_connection()
        c = conn.cursor()

        if len(keys) != len(self.available_keys):
            raise ValueError('Not enough keys')

        keys = list(self._key_dict_to_sequence(keys))
        key_dict = dict(zip(self.available_keys, keys))

        if not self.get_datasets(key_dict):
            raise exceptions.DatasetNotFoundError(f'No dataset found with keys {keys}')

        where_string = ' AND '.join([f'{key}=?' for key in self.available_keys])
        c.execute(f'DELETE FROM datasets WHERE {where_string}', keys)
        c.execute(f'DELETE FROM metadata WHERE {where_string}', keys)
