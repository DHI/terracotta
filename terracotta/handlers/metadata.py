from typing import Mapping, Sequence, Any, Union

from terracotta.drivers.base import Driver


def metadata(driver: Driver, keys: Union[Sequence[str], Mapping[str, str]]) -> Mapping[str, Any]:
    """Returns all metadata for a single dataset"""
    return driver.get_metadata(keys)
