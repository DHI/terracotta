from typing import Mapping, Sequence, Union, Any, List

import numpy as np

from terracotta import image
from terracotta.drivers.base import Driver


def colorbar(driver: Driver, keys: Union[Sequence[str], Mapping[str, str]], *,
             colormap: str = None, stretch_method: str = 'stretch',
             stretch_options: Mapping[str, Any] = None, num_values: int = 100
             ) -> Mapping[Union[int, float], List[float]]:
    """Returns a mapping pixel value -> rgba for given image"""
    stretch_options = stretch_options or {}

    with driver.connect():
        metadata = driver.get_metadata(keys)

    stretch_range = image.get_stretch_range(stretch_method, metadata, **stretch_options)
    pixel_values = np.linspace(stretch_range[0], stretch_range[1], num_values)
    colors = image.apply_cmap(pixel_values, stretch_range, cmap=colormap)
    return dict(*zip(pixel_values.tolist(), colors.tolist()))
