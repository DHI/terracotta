"""handlers/datasets.py

Handle /datasets API endpoint.
"""

from typing import Mapping, List, Union  # noqa: F401
from collections import OrderedDict
import re

from terracotta import get_settings, get_driver
from terracotta.profile import trace


@trace('datasets_handler')
def datasets(some_keys: Mapping[str, str] = None,
             page: int = 0, limit: int = 500) -> 'List[OrderedDict[str, str]]':
    """List all available key combinations"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    # TODO: Use some proper parsing
    if some_keys is not None:
        for key, value in some_keys.items():
            if re.match(r'^\[.*\]$', value):
                # This changes the typing of `some_keys`, as expected by `driver.get_datasets`,
                # but that makes mypy worried; hence the rather ugly # type: ignore
                some_keys[key] = value[1:-1].split(',')  # type: ignore

    with driver.connect():
        dataset_keys = driver.get_datasets(
            where=some_keys, page=page, limit=limit
        ).keys()
        key_names = driver.key_names

    return [OrderedDict(zip(key_names, ds_keys)) for ds_keys in dataset_keys]
