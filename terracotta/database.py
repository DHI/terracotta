from abc import ABC, abstractmethod
import functools
import itertools
import contextlib
import json
from typing import Callable, Any

import numpy as np


def requires_database(fun: Callable) -> Callable:
    @functools.wraps(fun)
    def inner(db: Database, *args, **kwargs) -> Any:
        with db.connect():
            fun(db, *args, **kwargs)
    return inner


class Database(ABC):
    @abstractmethod
    def __init__(self, url_or_path, *args, **kwargs):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def get(self, table, where=None, only=None):
        pass


class SQLiteDatabase(Database):
    def __init__(self, path, keys):
        self.path = path
        self.available_keys = keys

    @contextlib.contextmanager
    def connect(self):
        import sqlite3
        if self.conn is None:
            self.conn = sqlite3.connect(self.path)
        try:
            yield
        finally:
            self.conn.close()
            self.conn = None

    def create(self):
        if self.conn is None:
            raise RuntimeError('No open database connection')

        c = self.conn.cursor

        c.execute('CREATE TABLE keys (keys text)')
        c.executemany('INSERT INTO keys VALUES (?)', [(key,) for key in self.available_keys])

        key_string = ', '.join([f'{key} VARCHAR[255]' for key in self.available_keys])
        c.execute(f'CREATE TABLE metadata ({key_string}, wgs_bounds DOUBLE ARRAY[4], min DOUBLE, '
                  'max DOUBLE, percentiles FLOAT ARRAY[100], metadata TEXT)')
        self.conn.commit()

    def get(self, table, where=None, only=None):
        if self.conn is None:
            raise RuntimeError('No open database connection')

        only = only or '*'

        c = self.conn.cursor

        if where is None:
            c.execute('SELECT ? FROM ?', only, table)
        else:
            where_string = ' AND '.join(['?=?'] * len(where))
            items_flat = list(itertools.chain.from_iterable(where.items()))
            c.execute(f'SELECT ? FROM ? WHERE {where_string}', only, table, *items_flat)

        return dict(zip(only, c))

    def put(self, keys, filepath, metadata=None):
        if self.conn is None:
            raise RuntimeError('No open database connection')

        if len(keys) != len(self.available_keys):
            raise ValueError('Not enough keys')

        import rasterio
        from rasterio.warp import transform_bounds

        row_data = {'filepath': filepath}
        metadata = metadata or {}

        with rasterio.open(filepath) as src:
            raster_data = src.read(1)
            nodata = src.nodata
            bounds = transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds), densify_pts=21)

        row_data['wgs_bounds'] = bounds
        row_data['nodata'] = nodata
        if np.isnan(nodata):
            valid_data = raster_data[np.isfinite(raster_data)]
        else:
            valid_data = raster_data[raster_data != nodata]
        row_data['min'] = valid_data.min()
        row_data['max'] = valid_data.max()
        row_data['percentiles'] = np.percentile(valid_data, np.arange(1, 100))
        row_data['metadata'] = json.dumps(metadata)

        c = self.conn.cursor
        template_string = ', '.join(['?'] * (len(keys) + len(row_data)))
        c.execute(f'INSERT INTO metadata ({self.available_keys} {row_data.keys()}) VALUES ({template_string})', *keys + [row_data['wgs_bounds']])
        self.conn.commit()


class DynamoDBDatabase(Database):
    def __init__(self, url):
        import boto3
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])


DB_DRIVERS = {
    'sqlite': SQLiteDatabase,
    'dynamodb': DynamoDBDatabase
}


def get_database(url_or_path: str, provider: str = None) -> Database:
    if provider is None:  # try and auto-detect
        if url_or_path.startswith('s3://'):
            provider = 'dynamodb'
        else:
            provider = 'sqlite'

    try:
        DriverClass = DB_DRIVERS[provider]
    except KeyError as exc:
        raise ValueError(f'Unknown database provider {provider}') from exc

    return DriverClass(url_or_path)
