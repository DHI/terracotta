"""handlers/colormap.py

Handle /colormap API endpoint.
"""

from typing import List, Tuple, TypeVar, Dict, Any

import numpy as np

from terracotta.profile import trace

Number = TypeVar('Number', 'int', 'float')


@trace('colormap_handler')
def colormap(*, stretch_range: Tuple[Number, Number],
             colormap: str = None,
             num_values: int = 255) -> List[Dict[str, Any]]:
    """Returns a list [{value=pixel value, rgba=rgba tuple}] for given stretch parameters"""
    from terracotta import image

    target_coords = np.linspace(stretch_range[0], stretch_range[1], num_values)

    if colormap is not None:
        from terracotta.cmaps import get_cmap
        cmap = get_cmap(colormap)
    else:
        # assemble greyscale cmap of shape (255, 4)
        cmap = np.ones(shape=(255, 4), dtype='uint8') * 255
        cmap[:, :-1] = np.tile(np.arange(1, 256, dtype='uint8')[:, np.newaxis], (1, 3))

    cmap_coords = image.to_uint8(target_coords, *stretch_range) - 1
    colors = cmap[cmap_coords]

    return [dict(value=p, rgba=c) for p, c in zip(target_coords.tolist(), colors.tolist())]
