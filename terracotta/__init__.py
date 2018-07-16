"""__init__.py

Expose public API.
"""

# set version
try:
    # read from VERSION file if present
    import os
    with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
        __version__ = f.read().strip()
    del os
except OSError:
    # get through versioneer
    from terracotta._version import get_versions
    __version__ = get_versions()['version']
    del get_versions

# setup logging
import rasterio
import logging
logging.getLogger('rasterio').setLevel(logging.ERROR)
del rasterio, logging

# initialize settings
from typing import Mapping, Any
from terracotta.config import parse_config, TerracottaSettings

_settings = parse_config()


def update_settings(config: Mapping[str, Any] = None) -> None:
    from terracotta.config import parse_config
    global _settings
    _settings = parse_config(config)


def get_settings() -> TerracottaSettings:
    return _settings


del parse_config, TerracottaSettings
del Mapping, Any

# expose API
from terracotta.drivers import get_driver  # noqa: F401
