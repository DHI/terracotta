"""drivers/__init__.py

Define an interface to retrieve Terracotta drivers.
"""

from typing import Callable, Any, Union, Dict, Type
import functools
import urllib.parse as urlparse
from pathlib import Path

from terracotta.drivers.base import Driver


def singleton(fun: Callable) -> Callable:
    instance_cache: Dict[Any, Any] = {}

    @functools.wraps(fun)
    def inner(*args: Any, **kwargs: Any) -> Any:
        key = tuple(args) + tuple(kwargs.items())
        if key not in instance_cache:
            instance_cache[key] = fun(*args, **kwargs)
        return instance_cache[key]

    return inner


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


@singleton
def get_driver(url_or_path: Union[str, Path], provider: str = None) -> Driver:
    if provider is None:  # try and auto-detect
        provider = auto_detect_provider(url_or_path)

    DriverClass = load_driver(provider)

    return DriverClass(url_or_path)
