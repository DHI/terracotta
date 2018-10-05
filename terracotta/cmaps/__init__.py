"""cmaps/__init__.py

Define an interface to retrieve stored color maps.
"""

from typing.io import BinaryIO
from pkg_resources import resource_listdir, resource_stream, Requirement, DistributionNotFound

import numpy as np

SUFFIX = '_rgb.npy'

try:
    PACKAGE = Requirement.parse('terracotta')
    CMAP_FILES = resource_listdir(PACKAGE, 'terracotta/cmaps')

    def _get_cmap_data(name: str) -> BinaryIO:
        return resource_stream(PACKAGE, f'terracotta/cmaps/{name}{SUFFIX}')

except DistributionNotFound:  # terracotta was not installed, fall back to file system
    import os
    PACKAGE_DIR = os.path.dirname(__file__)
    CMAP_FILES = [os.path.basename(f) for f in os.listdir(PACKAGE_DIR)]

    def _get_cmap_data(name: str) -> BinaryIO:
        return open(os.path.join(PACKAGE_DIR, f'{name}{SUFFIX}'), 'rb')

AVAILABLE_CMAPS = sorted(set(f[:-len(SUFFIX)] for f in CMAP_FILES if f.endswith(SUFFIX)))


def get_cmap(name: str) -> np.ndarray:
    """Retrieve the given colormap and return RGB values as a uint8 NumPy array of shape (255, 3)"""
    name = name.lower()

    if name not in AVAILABLE_CMAPS:
        raise ValueError(f'Unknown colormap {name}, must be one of {AVAILABLE_CMAPS}')

    with _get_cmap_data(name) as f:
        cmap_data = np.load(f)

    assert cmap_data.shape == (255, 3)
    assert cmap_data.dtype == np.uint8
    return cmap_data
