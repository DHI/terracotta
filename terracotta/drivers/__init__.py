import functools

from terracotta.drivers.base import Driver
from terracotta.drivers.sqlite import SQLiteDriver


DRIVERS = {
    'sqlite': SQLiteDriver
}


def singleton(fun):
    instance_cache = {}

    @functools.wraps(fun)
    def inner(*args, **kwargs):
        key = tuple(args) + tuple(kwargs.items())
        if key not in instance_cache:
            instance_cache[key] = fun(*args, **kwargs)
        return instance_cache[key]

    return inner


@singleton
def get_driver(url_or_path: str, provider: str = None) -> Driver:
    if not provider:  # try and auto-detect
        provider = 'sqlite'

    try:
        DriverClass = DRIVERS[provider]
    except KeyError as exc:
        raise ValueError(f'Unknown database provider {provider}') from exc

    return DriverClass(url_or_path)
