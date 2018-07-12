"""handlers/legend.py

Handle /legend API endpoint.
"""

from typing import List, Tuple, TypeVar, Dict, Any

import numpy as np

from terracotta import image

Number = TypeVar('Number', 'int', 'float')


def legend(*, colormap: str, stretch_range: Tuple[Number, Number],
           num_values: int = 100) -> List[Dict[str, Any]]:
    """Returns a list [(pixel value, rgba)] for given stretch parameters"""
    pixel_values = np.linspace(stretch_range[0], stretch_range[1], num_values)
    colors = image.apply_cmap(pixel_values, stretch_range, cmap=colormap)
    return [dict(value=p, rgba=c) for p, c in zip(pixel_values.tolist(), colors.tolist())]
