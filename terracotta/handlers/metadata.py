from typing import Mapping, Sequence, Any, Union

from terracotta import get_settings, get_driver


def metadata(keys: Union[Sequence[str], Mapping[str, str]]) -> Mapping[str, Any]:
    """Returns all metadata for a single dataset"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)
    return driver.get_metadata(keys)
