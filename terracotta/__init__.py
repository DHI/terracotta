
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

import matplotlib as mpl
mpl.use('Agg')
del mpl
