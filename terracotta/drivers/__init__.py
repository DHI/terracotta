from terracotta.drivers.base import Driver
from terracotta.drivers.sqlite import SQLiteDriver


DRIVERS = {
    'sqlite': SQLiteDriver
}


def get_driver(url_or_path: str, provider: str = None) -> Driver:
    if provider is None:  # try and auto-detect
        provider = 'sqlite'

    try:
        DriverClass = DRIVERS[provider]
    except KeyError as exc:
        raise ValueError(f'Unknown database provider {provider}') from exc

    return DriverClass(url_or_path)
