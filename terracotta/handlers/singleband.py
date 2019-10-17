"""handlers/singleband.py

Handle /singleband API endpoint.
"""

from typing import Sequence, Mapping, Union, Tuple, Optional, TypeVar, cast
from typing.io import BinaryIO

import collections

from terracotta import get_settings, get_driver, image, xyz
from terracotta.profile import trace

Number = TypeVar('Number', int, float)
RGBA = Tuple[Number, Number, Number, Number]


@trace('singleband_handler')
def singleband(keys: Union[Sequence[str], Mapping[str, str]],
               tile_xyz: Tuple[int, int, int] = None, *,
               colormap: Union[str, Mapping[Number, RGBA], None] = None,
               stretch_range: Tuple[Number, Number] = None,
               tile_size: Tuple[int, int] = None) -> BinaryIO:
    """Return singleband image as PNG"""

    cmap_or_palette: Union[str, Sequence[RGBA], None]

    if stretch_range is None:
        stretch_min, stretch_max = None, None
    else:
        stretch_min, stretch_max = stretch_range

    preserve_values = isinstance(colormap, collections.Mapping)

    settings = get_settings()
    if tile_size is None:
        tile_size = settings.DEFAULT_TILE_SIZE

    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    with driver.connect():
        metadata = driver.get_metadata(keys)
        tile_data = xyz.get_tile_data(
            driver, keys, tile_xyz,
            tile_size=tile_size, preserve_values=preserve_values
        )

    if preserve_values:
        # bin output image into supplied labels, starting at 1
        colormap = cast(Mapping, colormap)

        labels, label_colors = list(colormap.keys()), list(colormap.values())

        cmap_or_palette = label_colors
        out = image.label(tile_data, labels)
    else:
        # determine stretch range from metadata and arguments
        stretch_range_ = list(metadata['range'])

        if stretch_min is not None:
            stretch_range_[0] = stretch_min

        if stretch_max is not None:
            stretch_range_[1] = stretch_max

        cmap_or_palette = cast(Optional[str], colormap)
        out = image.to_uint8(tile_data, *stretch_range_)

    return image.array_to_png(out, colormap=cmap_or_palette)
