"""handlers/datasets.py

Handle /datasets API endpoint.
"""

from typing import List, Mapping, Dict

from terracotta import get_settings, get_driver
from terracotta.profile import trace


@trace()
def datasets(some_keys: Mapping[str, str] = None) -> List[Dict[str, str]]:
    """List all available key combinations"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    with driver.connect():
        dataset_keys = driver.get_datasets(where=some_keys).keys()
        key_names = driver.available_keys

    return [dict(zip(key_names, ds_keys)) for ds_keys in dataset_keys]
