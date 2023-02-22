"""__init__.py

Initialize global setup
"""

# get version
try:
    from terracotta._version import version as __version__  # noqa: F401
except ImportError:  # pragma: no cover
    # package is not installed
    raise RuntimeError(
        'Terracotta has not been installed correctly. Please run `pip install -e .` or '
        '`python setup.py develop` in the Terracotta package folder.'
    ) from None


# initialize settings, define settings API
from typing import Mapping, Any, Set
from terracotta.config import parse_config, TerracottaSettings

_settings: TerracottaSettings = parse_config()
_overwritten_settings: Set = set()


def update_settings(**new_config: Any) -> None:
    """Update the global Terracotta runtime settings.

    Arguments:

        new_config: Options to override. Have to be valid Terracotta settings.

    Example:

        >>> import terracotta as tc
        >>> tc.get_settings().DEFAULT_TILE_SIZE
        (256, 256)
        >>> tc.update_settings(DEFAULT_TILE_SIZE=[512, 512])
        >>> tc.get_settings().DEFAULT_TILE_SIZE
        (512, 512)

    """
    from terracotta.config import parse_config
    global _settings, _overwritten_settings
    current_config = {k: getattr(_settings, k) for k in _overwritten_settings}
    _settings = parse_config({**current_config, **new_config})
    _overwritten_settings |= set(new_config.keys())


def get_settings() -> TerracottaSettings:  # noqa: F821
    """Returns the current set of global runtime settings.

    Example:

        >>> import terracotta as tc
        >>> tc.get_settings().DEBUG
        False

    """
    return _settings


del parse_config, TerracottaSettings
del Mapping, Any, Set


# expose API
from terracotta.drivers import get_driver  # noqa: F401

__all__ = (
    'get_driver',
    'get_settings',
    'update_settings',
)
