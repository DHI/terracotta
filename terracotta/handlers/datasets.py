from typing import List, Mapping

from terracotta.drivers.base import Driver


def datasets(driver: Driver, some_keys: Mapping[str, str] = None) -> List[List[str]]:
    """List all available key combinations"""
    with driver.connect():
        return [list(ds) for ds in driver.get_datasets(where=some_keys).keys()]
