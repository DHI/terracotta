"""handlers/legend.py

Handle /legend API endpoint.
"""

from typing import List, Tuple, TypeVar, Dict, Any

import numpy as np

from terracotta.profile import trace

Number = TypeVar('Number', 'int', 'float')


@trace('legend_handler')
def legend(*, stretch_range: Tuple[Number, Number],
           colormap: str = None,
           num_values: int = 255) -> List[Dict[str, Any]]:
    """Returns a list [{value=pixel value, rgb=rgb tuple}] for given stretch parameters"""
    target_coords = np.linspace(stretch_range[0], stretch_range[1], num_values)

    if colormap is not None:
        from terracotta.cmaps import get_cmap
        cmap = get_cmap(colormap)
    else:
        # assemble greyscale cmap of shape (255, 3)
        cmap = np.tile(np.arange(1, 256, dtype='uint8')[:, np.newaxis], (1, 3))

    cmap_coords = np.around(np.linspace(0, len(cmap) - 1, num_values)).astype('uint8')
    colors = cmap[cmap_coords]

    return [dict(value=p, rgb=c) for p, c in zip(target_coords.tolist(), colors.tolist())]
