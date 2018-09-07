"""handlers/keys.py

Handle /keys API endpoint.
"""

from typing import List

from terracotta import get_settings, get_driver
from terracotta.profile import trace


@trace()
def keys() -> List[str]:
    """List available keys, in order"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)
    return driver.available_keys
