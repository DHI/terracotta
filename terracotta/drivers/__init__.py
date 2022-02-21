"""drivers/__init__.py

Define an interface to retrieve Terracotta drivers.
"""

import os
from typing import Union, Tuple, Dict, Type
import urllib.parse as urlparse
from pathlib import Path

from terracotta.drivers.base_classes import MetaStore
from terracotta.drivers.terracotta_driver import TerracottaDriver
from terracotta.drivers.geotiff_raster_store import GeoTiffRasterStore

URLOrPathType = Union[str, Path]


def load_driver(provider: str) -> Type[MetaStore]:
    if provider == 'sqlite-remote':
        from terracotta.drivers.sqlite_remote_meta_store import RemoteSQLiteMetaStore
        return RemoteSQLiteMetaStore

    if provider == 'mysql':
        from terracotta.drivers.mysql_meta_store import MySQLMetaStore
        return MySQLMetaStore

    if provider == 'sqlite':
        from terracotta.drivers.sqlite_meta_store import SQLiteMetaStore
        return SQLiteMetaStore

    raise ValueError(f'Unknown database provider {provider}')


def auto_detect_provider(url_or_path: str) -> str:
    parsed_path = urlparse.urlparse(url_or_path)

    scheme = parsed_path.scheme
    if scheme == 's3':
        return 'sqlite-remote'

    if scheme == 'mysql':
        return 'mysql'

    return 'sqlite'


_DRIVER_CACHE: Dict[Tuple[URLOrPathType, str, int], TerracottaDriver] = {}


def get_driver(url_or_path: URLOrPathType, provider: str = None) -> TerracottaDriver:
    """Retrieve Terracotta driver instance for the given path.

    This function always returns the same instance for identical inputs.

    Warning:

       Always retrieve Driver instances through this function instead of
       instantiating them directly to prevent caching issues.

    Arguments:

        url_or_path: A path identifying the database to connect to.
            The expected format depends on the driver provider.
        provider: Driver provider to use (one of sqlite, sqlite-remote, mysql;
            default: auto-detect).

    Example:

        >>> import terracotta as tc
        >>> tc.get_driver('tc.sqlite')
        TerracottaDriver(
            meta_store=SQLiteDriver('/home/terracotta/tc.sqlite'),
            raster_store=GeoTiffRasterStore()
        )
        >>> tc.get_driver('mysql://root@localhost/tc')
        TerracottaDriver(
            meta_store=MySQLDriver('mysql+pymysql://localhost:3306/tc'),
            raster_store=GeoTiffRasterStore()
        )
        >>> # pass provider if path is given in a non-standard way
        >>> tc.get_driver('root@localhost/tc', provider='mysql')
        TerracottaDriver(
            meta_store=MySQLDriver('mysql+pymysql://localhost:3306/tc'),
            raster_store=GeoTiffRasterStore()
        )

    """
    url_or_path = str(url_or_path)

    if provider is None:  # try and auto-detect
        provider = auto_detect_provider(url_or_path)

    DriverClass = load_driver(provider)
    normalized_path = DriverClass._normalize_path(url_or_path)
    cache_key = (normalized_path, provider, os.getpid())

    if cache_key not in _DRIVER_CACHE:
        driver = TerracottaDriver(
            meta_store=DriverClass(url_or_path),
            raster_store=GeoTiffRasterStore()
        )
        _DRIVER_CACHE[cache_key] = driver

    return _DRIVER_CACHE[cache_key]
