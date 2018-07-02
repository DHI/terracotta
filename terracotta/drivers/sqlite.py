"""sqlite.py

SQLite-backed data handler. Metadata is stored in an SQLite database, raster data is assumed
to be present on disk.
"""

import operator
import contextlib
import json
import re
from typing import Any, Sequence, Mapping, Tuple, Union

from cachetools import LRUCache, cachedmethod
import numpy as np

from terracotta.drivers.base import RasterDriver, requires_connection
from terracotta import settings


class SQLiteDriver(RasterDriver):
    KEY_TYPE: str = 'VARCHAR[256]'
    METADATA_COLUMNS: Tuple[Tuple[str]] = (
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

    def __init__(self, path: str):
        self.path = path
        self._available_keys = None
        self.conn = None

        self._metadata_cache = LRUCache(settings.CACHE_SIZE)
        super(SQLiteDriver, self).__init__()

    @staticmethod
    def _encode_data(decoded: Mapping[str, Any]) -> Mapping[str, Any]:
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
            'percentiles': decoded['percentiles'].tostring(),
            'metadata': json.dumps(decoded['metadata'])
        }
        return encoded

    @staticmethod
    def _decode_data(encoded: Mapping[str, Any]) -> Mapping[str, Any]:
        """Transform from database format to internal representation"""
        decoded = {
            'bounds': tuple([encoded[f'bounds_{d}'] for d in ('north', 'east', 'south', 'west')]),
            'nodata': encoded['nodata'],
            'range': (encoded['min'], encoded['max']),
            'mean': encoded['mean'],
            'stdev': encoded['stdev'],
            'percentiles': np.fromstring(encoded['percentiles']),
            'metadata': json.loads(encoded['metadata'])
        }
        return decoded

    def _key_dict_to_sequence(self, keys):
        try:
            return [keys[key] for key in self.available_keys]
        except TypeError:  # not a mapping
            return keys
        except KeyError as exc:
            raise ValueError('Encountered unknown key') from exc

    @contextlib.contextmanager
    def connect(self):
        import sqlite3
        if self.conn is None:
            self.conn = sqlite3.connect(self.path)
        try:
            yield
        finally:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    @requires_connection
    def _get_available_keys(self) -> Tuple[str]:
        if self._available_keys is None:
            c = self.conn.cursor()
            c.execute('SELECT * FROM keys')
            self._available_keys = tuple(row[0] for row in c)
        return self._available_keys

    available_keys = property(_get_available_keys)

    @requires_connection
    def create(self, keys: Sequence[str], drop_if_exists: bool = False):
        if not all(re.match(r'\w+', key) for key in keys):
            raise ValueError('keys can be alphanumeric only')

        c = self.conn.cursor()

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
        column_string = ', '.join(f'{col} {col_type}' for col, col_type in self.METADATA_COLUMNS)
        c.execute(f'CREATE TABLE metadata ({key_string}, {column_string}, '
                  f'PRIMARY KEY ({", ".join(keys)}))')

        self.conn.commit()

    @cachedmethod(operator.attrgetter('_metadata_cache'))
    @requires_connection
    def _get_datasets(self, where: Tuple[Tuple[str], Tuple[str]] = None):
        c = self.conn.cursor()

        if where is None:
            c.execute(f'SELECT * FROM datasets')
        else:
            where_keys, where_values = where
            if not all(key in self.available_keys for key in where_keys):
                raise ValueError('Encountered unrecognized keys in where clause')
            where_string = ' AND '.join([f'{key}=?' for key in where_keys])
            c.execute(f'SELECT * FROM datasets WHERE {where_string}', where_values)

        num_keys = len(self.available_keys)
        return {tuple(row[:num_keys]): row[-1] for row in c}

    def get_datasets(self, where: Mapping[str, str] = None) -> Sequence[Mapping[str, Any]]:
        if where is not None:
            where = (tuple(where.keys()), tuple(where.values()))
        return self._get_datasets(where)

    @cachedmethod(operator.attrgetter('_metadata_cache'))
    @requires_connection
    def _get_metadata(self, keys: Tuple[str]) -> Mapping[str, Any]:
        c = self.conn.cursor()

        where_string = ' AND '.join([f'{key}=?' for key in self.available_keys])
        c.execute(f'SELECT * FROM metadata WHERE {where_string}', keys)

        rows = list(c)
        if not rows:  # support lazy loading
            filepath = self.get_datasets(dict(zip(self.available_keys, keys)))
            if not filepath:
                raise ValueError(f'No dataset found for given keys {keys}')
            assert len(filepath) == 1
            # compute metadata and try again
            self.insert(keys, filepath[keys])
            c.execute(f'SELECT * FROM metadata WHERE {where_string}', keys)
            rows = list(c)

        data_columns, _ = zip(*self.METADATA_COLUMNS)
        encoded_data = [dict(zip(self.available_keys + data_columns, row)) for row in rows]
        assert len(encoded_data) == 1
        return self._decode_data(encoded_data[0])

    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Mapping[str, Any]:
        keys = tuple(self._key_dict_to_sequence(keys))
        return self._get_metadata(keys)

    @requires_connection
    def insert(self, keys: Union[Sequence[str], Mapping[str, str]],
               filepath: str, metadata: Mapping[str, Any] = None, compute_metadata: bool = True):
        if len(keys) != len(self.available_keys):
            raise ValueError('Not enough keys')

        c = self.conn.cursor()

        keys = list(self._key_dict_to_sequence(keys))
        template_string = ', '.join(['?'] * (len(keys) + 1))
        c.execute(f'INSERT OR REPLACE INTO datasets VALUES ({template_string})', keys + [filepath])

        if not compute_metadata:
            return

        row_data = self._compute_metadata(filepath, metadata)
        encoded_data = self._encode_data(row_data)

        row_keys, row_values = zip(*encoded_data.items())
        template_string = ', '.join(['?'] * (len(keys) + len(row_values)))
        c.execute(f'INSERT OR REPLACE INTO metadata ({", ".join(self.available_keys)}, '
                  f'{", ".join(row_keys)}) VALUES ({template_string})', keys + list(row_values))
