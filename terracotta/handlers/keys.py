"""handlers/keys.py

Handle /keys API endpoint.
"""

from typing import List, Dict

from terracotta import get_settings, get_driver
from terracotta.profile import trace


@trace('keys_handler')
def keys() -> List[Dict[str, str]]:
    """List available keys, in order"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    response = []
    for key, description in driver.get_keys().items():
        response_row = {'key': key}
        if description:
            response_row['description'] = description

        response.append(response_row)

    return response
