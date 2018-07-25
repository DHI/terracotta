"""__init__.py

Initialize settings and expose public API.
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


# setup environment
import os
os.environ.update(
    GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'  # do not look for auxiliary files
)
del os


# setup logging
import rasterio
import logging
logging.getLogger('rasterio').setLevel(logging.ERROR)
del rasterio, logging


# initialize settings
from typing import Mapping, Any, Set
from terracotta.config import parse_config, TerracottaSettings

_settings: TerracottaSettings = parse_config()
_overwritten_settings: Set = set()


def update_settings(**new_config: Any) -> None:
    from terracotta.config import parse_config
    global _settings, _overwritten_settings
    current_config = {k: getattr(_settings, k) for k in _overwritten_settings}
    _settings = parse_config({**current_config, **new_config})
    _overwritten_settings |= set(new_config.keys())


def get_settings() -> TerracottaSettings:
    return _settings


del parse_config, TerracottaSettings
del Mapping, Any, Set


# expose API
from terracotta.drivers import get_driver  # noqa: F401
