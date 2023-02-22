"""drivers/__init__.py

Define an interface to retrieve Terracotta drivers.
"""

from typing import Union, Tuple, Dict, Type
import urllib.parse as urlparse
from pathlib import Path

from terracotta.drivers.base import Driver

URLOrPathType = Union[str, Path]


def load_driver(provider: str) -> Type[Driver]:
    if provider == 'sqlite-remote':
        from terracotta.drivers.sqlite_remote import RemoteSQLiteDriver
        return RemoteSQLiteDriver

    if provider == 'mysql':
        from terracotta.drivers.mysql import MySQLDriver
        return MySQLDriver

    if provider == 'sqlite':
        from terracotta.drivers.sqlite import SQLiteDriver
        return SQLiteDriver

    raise ValueError(f'Unknown database provider {provider}')


def auto_detect_provider(url_or_path: Union[str, Path]) -> str:
    parsed_path = urlparse.urlparse(str(url_or_path))

    scheme = parsed_path.scheme
    if scheme == 's3':
        return 'sqlite-remote'

    if scheme == 'mysql':
        return 'mysql'

    return 'sqlite'


_DRIVER_CACHE: Dict[Tuple[URLOrPathType, str], Driver] = {}


def get_driver(url_or_path: URLOrPathType, provider: str = None) -> Driver:
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
        SQLiteDriver('/home/terracotta/tc.sqlite')
        >>> tc.get_driver('mysql://root@localhost/tc')
        MySQLDriver('mysql://root@localhost:3306/tc')
        >>> # pass provider if path is given in a non-standard way
        >>> tc.get_driver('root@localhost/tc', provider='mysql')
        MySQLDriver('mysql://root@localhost:3306/tc')

    """
    if provider is None:  # try and auto-detect
        provider = auto_detect_provider(url_or_path)

    if isinstance(url_or_path, Path) or provider == 'sqlite':
        url_or_path = str(Path(url_or_path).resolve())

    DriverClass = load_driver(provider)
    normalized_path = DriverClass._normalize_path(url_or_path)
    cache_key = (normalized_path, provider)

    if cache_key not in _DRIVER_CACHE:
        _DRIVER_CACHE[cache_key] = DriverClass(url_or_path)

    return _DRIVER_CACHE[cache_key]
