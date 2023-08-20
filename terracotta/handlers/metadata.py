"""handlers/metadata.py

Handle /metadata API endpoint.
"""

from typing import Mapping, Sequence, Dict, Any, Union, List, Optional
from collections import OrderedDict

from terracotta import get_settings, get_driver
from terracotta.exceptions import InvalidArgumentsError
from terracotta.profile import trace


def filter_metadata(
    metadata: Dict[str, Any], columns: Optional[List[str]]
) -> Dict[str, Any]:
    """Filter metadata by columns, if given"""
    assert (
        columns is None or len(columns) > 0
    ), "columns must either be a non-empty list or None"

    if columns:
        metadata = {c: metadata[c] for c in columns}

    return metadata


@trace("metadata_handler")
def metadata(
    columns: Optional[List[str]], keys: Union[Sequence[str], Mapping[str, str]]
) -> Dict[str, Any]:
    """Returns all metadata for a single dataset"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)
    metadata = filter_metadata(driver.get_metadata(keys), columns)
    metadata["keys"] = OrderedDict(zip(driver.key_names, keys))
    return metadata


@trace("multiple_metadata_handler")
def multiple_metadata(
    columns: Optional[List[str]], datasets: List[List[str]]
) -> List[Dict[str, Any]]:
    """Returns all metadata for multiple datasets"""
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)
    key_names = driver.key_names

    if len(datasets) > settings.MAX_POST_METADATA_KEYS:
        raise InvalidArgumentsError(
            f"Maximum number of keys exceeded ({settings.MAX_POST_METADATA_KEYS}). "
            f"This limit can be configured in the server settings."
        )

    out = []
    with driver.connect():
        for dataset in datasets:
            metadata = filter_metadata(driver.get_metadata(dataset), columns)
            metadata["keys"] = OrderedDict(zip(key_names, dataset))
            out.append(metadata)

    return out
