"""drivers/__init__.py

Define an interface to retrieve Terracotta drivers.
"""

from typing import Callable, Any, Dict, Union
import functools
import urllib.parse as urlparse
from pathlib import Path

from terracotta.drivers.base import Driver
from terracotta.drivers.sqlite import SQLiteDriver
from terracotta.drivers.sqlite_remote import RemoteSQLiteDriver


DRIVERS = {
    'sqlite': SQLiteDriver,
    'sqlite-remote': RemoteSQLiteDriver
}


def singleton(fun: Callable) -> Callable:
    instance_cache: Dict[Any, Any] = {}

    @functools.wraps(fun)
    def inner(*args: Any, **kwargs: Any) -> Any:
        key = tuple(args) + tuple(kwargs.items())
        if key not in instance_cache:
            instance_cache[key] = fun(*args, **kwargs)
        return instance_cache[key]

    return inner


def auto_detect_provider(url_or_path: Union[str, Path]) -> str:
    parsed_path = urlparse.urlparse(str(url_or_path))

    if parsed_path.scheme == 's3':
        return 'sqlite-remote'

    return 'sqlite'


@singleton
def get_driver(url_or_path: Union[str, Path], provider: str = None) -> Driver:
    if provider is None:  # try and auto-detect
        provider = auto_detect_provider(url_or_path)

    try:
        DriverClass = DRIVERS[provider]
    except KeyError as exc:
        raise ValueError(f'Unknown database provider {provider}') from exc

    return DriverClass(url_or_path)
