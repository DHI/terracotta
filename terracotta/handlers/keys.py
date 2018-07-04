from typing import List

from terracotta import settings, get_driver


def keys() -> List[str]:
    """List available keys, in order"""
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)
    return driver.available_keys
