from typing import Sequence, Mapping, Any, Union
from typing.io import BinaryIO

from terracotta.drivers.base import Driver
from terracotta import settings, image, xyz


def singleband(driver: Driver, keys: Union[Sequence[str], Mapping[str, str]],
               tile_xyz: Sequence[int], *, colormap: str = None, stretch_method: str = 'stretch',
               stretch_options: Mapping[str, Any] = None) -> BinaryIO:
    """Return singleband image as PNG"""

    stretch_options = stretch_options or {}

    try:
        tile_x, tile_y, tile_z = tile_xyz
    except ValueError:
        raise ValueError('xyz argument must contain three values')

    with driver.connect():
        metadata = driver.get_metadata(keys)
        tile_size = settings.TILE_SIZE
        tile_data = xyz.get_tile_data(driver, keys, tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                      tilesize=tile_size)
    valid_mask = image.get_valid_mask(tile_data, nodata=metadata['nodata'])
    stretch_range = image.get_stretch_range(stretch_method, metadata, **stretch_options)
    out = image.to_uint8(tile_data, *stretch_range, cmap=colormap)
    alpha_mask = (255 * valid_mask).astype('uint8')
    return image.array_to_png(out, alpha_mask=alpha_mask)
