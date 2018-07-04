from typing import List, Mapping

from terracotta import settings, get_driver


def datasets(some_keys: Mapping[str, str] = None) -> List[List[str]]:
    """List all available key combinations"""
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)
    with driver.connect():
        return [list(ds) for ds in driver.get_datasets(where=some_keys).keys()]
