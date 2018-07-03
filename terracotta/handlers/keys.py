from typing import List

from terracotta.drivers.base import Driver


def keys(driver: Driver) -> List[str]:
    """List available keys, in order"""
    return driver.available_keys
