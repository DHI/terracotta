"""__init__.py

Initialize global setup
"""

try:
    from terracotta._version import version as __version__  # noqa: F401
except ImportError:
    # package is not installed
    raise RuntimeError(
        'Terracotta has not been installed correctly. Please run `pip install -e .` or '
        '`python setup.py install` in the Terracotta package folder.'
    ) from None


# setup environment
import os
os.environ.update(
    GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'  # do not look for auxiliary files
)
del os


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
