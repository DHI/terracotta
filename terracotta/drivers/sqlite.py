"""sqlite.py

SQLite-backed data handler. Metadata is stored in an SQLite database, raster data is assumed
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
import urllib.parse as urlparse
from threading import Lock, get_ident
from pathlib import Path
import sqlite3
from sqlite3 import Connection

from cachetools import LFUCache, cachedmethod
import numpy as np

from terracotta.drivers.base import RasterDriver, requires_connection
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


def _download_from_s3(bucket_name: str, key: str, location: str) -> None:
    import boto3
    import botocore
    s3 = boto3.resource('s3')
    try:
        s3.Bucket(bucket_name).download_file(key, location)
    except botocore.exceptions.ClientError as exc:
        raise exceptions.InvalidDatabaseError('Could not retrieve database from S3') from exc


class SQLiteDriver(RasterDriver):
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
        settings = get_settings()

        # check if database needs to be retrieved from remote storage
        path_str = str(path)
        if path_str.startswith('s3://'):
            remote_db_path = os.path.join(settings.DB_CACHEDIR, 's3_db.sqlite')
            if not os.path.isfile(remote_db_path):
                os.makedirs(settings.DB_CACHEDIR, exist_ok=True)
                parsed_url = urlparse.urlparse(path_str)
                bucket_name, key = parsed_url.netloc, parsed_url.path.strip('/')
                _download_from_s3(bucket_name, key, remote_db_path)
            path_str = remote_db_path

        self.path: str = path_str
        self._connetion_pool: Dict[int, Connection] = {}
        self._db_lock: Lock = Lock()
        self._metadata_cache: LFUCache = LFUCache(settings.CACHE_SIZE, getsizeof=sys.getsizeof)
        super(SQLiteDriver, self).__init__(path)

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
        return self._connetion_pool[get_ident()]

    @contextlib.contextmanager
    def lock_for_write(self) -> Iterator:
        conn = self.get_connection()
        with self._db_lock:
            yield
            conn.commit()

    @contextlib.contextmanager
    def connect(self) -> Iterator:
        thread_id = get_ident()
        conn = self._connetion_pool.get(thread_id)
        if conn is None:
            with convert_exceptions('Unable to connect to database'):
                conn = sqlite3.connect(self.path)
            self._connetion_pool[thread_id] = conn
            close = True
        else:
            close = False
        try:
            yield
        finally:
            conn.commit()
            if close:
                conn.close()
                self._connetion_pool.pop(thread_id)

    @memoize
    @convert_exceptions('Could not retrieve keys from database')
    @requires_connection
    def _get_available_keys(self) -> Tuple[str, ...]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM keys')
        return tuple(row[0] for row in c)

    available_keys = property(_get_available_keys)  # type: ignore

    @convert_exceptions('Could not create tables')
    @requires_connection
    def create(self, keys: Sequence[str], drop_if_exists: bool = False, lock: bool = True) -> None:
        if not all(re.match(r'\w+', key) for key in keys):
            raise ValueError('keys can be alphanumeric only')

        with self.lock_for_write():
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
    @convert_exceptions('Could not retrieve datasets')
    @requires_connection
    def _get_datasets(self,
                      where: Tuple[Tuple[str], Tuple[str]] = None) -> Dict[Tuple[str, ...], str]:
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

    def get_datasets(self, where: Mapping[str, str] = None) -> Dict[Tuple[str, ...], str]:
        where_ = where and (tuple(where.keys()), tuple(where.values()))
        return self._get_datasets(where_)

    @cachedmethod(operator.attrgetter('_metadata_cache'))
    @convert_exceptions('Could not retrieve metadata')
    @requires_connection
    def _get_metadata(self, keys: Tuple[str]) -> Dict[str, Any]:
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
            self.insert(keys, filepath[keys])
            c.execute(f'SELECT * FROM metadata WHERE {where_string}', keys)
            rows = list(c)

        data_columns, _ = zip(*self.METADATA_COLUMNS)
        encoded_data = [dict(zip(self.available_keys + data_columns, row)) for row in rows]
        assert len(encoded_data) == 1
        return self._decode_data(encoded_data[0])

    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
        keys = tuple(self._key_dict_to_sequence(keys))
        return self._get_metadata(keys)

    @convert_exceptions('Could not write to database')
    @requires_connection
    def insert(self, keys: Union[Sequence[str], Mapping[str, str]], filepath: str,
               metadata: Mapping[str, Any] = None, *, compute_metadata: bool = True,
               override_path: str = None) -> None:
        conn = self.get_connection()
        c = conn.cursor()

        if len(keys) != len(self.available_keys):
            raise ValueError('Not enough keys')

        if override_path is None:
            override_path = filepath

        with self.lock_for_write():
            keys = list(self._key_dict_to_sequence(keys))
            template_string = ', '.join(['?'] * (len(keys) + 1))
            c.execute(f'INSERT OR REPLACE INTO datasets VALUES ({template_string})',
                      keys + [override_path])

        if not compute_metadata:
            return

        row_data = self._compute_metadata(filepath, metadata)
        encoded_data = self._encode_data(row_data)

        with self.lock_for_write():
            row_keys, row_values = zip(*encoded_data.items())
            template_string = ', '.join(['?'] * (len(keys) + len(row_values)))
            c.execute(f'INSERT OR REPLACE INTO metadata ({", ".join(self.available_keys)}, '
                      f'{", ".join(row_keys)}) VALUES ({template_string})', keys + list(row_values))
