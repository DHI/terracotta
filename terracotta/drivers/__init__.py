"""drivers/__init__.py

Define an interface to retrieve Terracotta drivers.
"""

from typing import Callable, Any, Union, Dict, Optional, NamedTuple, cast
import functools
import urllib.parse as urlparse
from pathlib import Path
import re

from terracotta.drivers.base import Driver
from terracotta.drivers.sqlite import SQLiteDriver
from terracotta.drivers.sqlite_remote import RemoteSQLiteDriver
from terracotta.drivers.mysql import MySQLDriver


DRIVERS = {
    'sqlite': SQLiteDriver,
    'sqlite-remote': RemoteSQLiteDriver,
    'mysql': MySQLDriver
}


class ConnectionInfo(NamedTuple):
    user: str
    password: str
    host: str
    port: Optional[int]


def parse_connection(con_str: str) -> Optional[ConnectionInfo]:
    con_reg = re.compile('(\w*?):?(\w+)@([^\s:]+):?([0-9]*)')
    m = con_reg.match(con_str)

    if m is None:
        return None

    port: Optional[int]
    try:
        port = int(m.group(4))
    except ValueError:
        port = None

    return ConnectionInfo(user=m.group(1), password=m.group(2),
                          host=m.group(3), port=port)


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

    if parse_connection(str(url_or_path)) is not None:
        return 'mysql'

    return 'sqlite'


@singleton
def get_driver(url_or_path: Union[str, Path], provider: str = None) -> Driver:
    if provider is None:  # try and auto-detect
        provider = auto_detect_provider(url_or_path)

    try:
        DriverClass = DRIVERS[provider]
    except KeyError as exc:
        raise ValueError(f'Unknown database provider {provider}') from exc

    if DriverClass is MySQLDriver:
        con_info = cast(ConnectionInfo, parse_connection(str(url_or_path)))  # We know it's not None
        port = con_info.port or 0
        return DriverClass(host=con_info.host, user=con_info.user,
                           password=con_info.password, port=port)

    return DriverClass(url_or_path)
