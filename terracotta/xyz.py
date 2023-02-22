"""xyz.py

Utilities to work with XYZ Mercator tiles.
"""

from typing import Sequence, Union, Mapping, Tuple, Any

import mercantile

from terracotta import exceptions
from terracotta.drivers.base import Driver


# TODO: add accurate signature if mypy ever supports conditional return types
def get_tile_data(driver: Driver,
                  keys: Union[Sequence[str], Mapping[str, str]],
                  tile_xyz: Tuple[int, int, int] = None,
                  *, tile_size: Tuple[int, int] = (256, 256),
                  preserve_values: bool = False,
                  asynchronous: bool = False) -> Any:
    """Retrieve raster image from driver for given XYZ tile and keys"""

    if tile_xyz is None:
        # read whole dataset
        return driver.get_raster_tile(
            keys, tile_size=tile_size, preserve_values=preserve_values,
            asynchronous=asynchronous
        )

    # determine bounds for given tile
    metadata = driver.get_metadata(keys)
    wgs_bounds = metadata['bounds']

    tile_x, tile_y, tile_z = tile_xyz

    if not tile_exists(wgs_bounds, tile_x, tile_y, tile_z):
        raise exceptions.TileOutOfBoundsError(
            f'Tile {tile_z}/{tile_x}/{tile_y} is outside image bounds'
        )

    mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
    target_bounds = mercantile.xy_bounds(mercator_tile)

    return driver.get_raster_tile(
        keys, tile_bounds=target_bounds, tile_size=tile_size,
        preserve_values=preserve_values, asynchronous=asynchronous
    )


def tile_exists(bounds: Sequence[float], tile_x: int, tile_y: int, tile_z: int) -> bool:
    """Check if an XYZ tile is inside the given physical bounds."""
    mintile = mercantile.tile(bounds[0], bounds[3], tile_z)
    maxtile = mercantile.tile(bounds[2], bounds[1], tile_z)

    return mintile.x <= tile_x <= maxtile.x and mintile.y <= tile_y <= maxtile.y
