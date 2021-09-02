"""handlers/valid_values.py

Handle /valid_values API endpoint.
"""

from typing import Dict, Mapping, List, Union

from terracotta import get_settings, get_driver
from terracotta.profile import trace


@trace('valid_values_handler')
def valid_values(some_keys: Mapping[str, Union[str, List[str]]] = None) -> Dict[str, List[str]]:
    """List all available valid values"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    with driver.connect():
        valid_values = driver.get_valid_values(some_keys or {})

    return valid_values
