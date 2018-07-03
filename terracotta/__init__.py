
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

import matplotlib as mpl
mpl.use('Agg')
del mpl


def update_settings(config=None):
    from terracotta.config import get_settings
    global settings
    settings = get_settings(config)


settings = None
update_settings()

from terracotta.drivers import get_driver  # noqa: F401
