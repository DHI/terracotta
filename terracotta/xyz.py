"""xyz.py

Utilities to work with XYZ Mercator tiles.
"""

from typing import Sequence, Tuple, Union, Mapping

import numpy as np
import mercantile

from terracotta import exceptions
from terracotta.drivers.base import Driver


def get_tile_data(driver: Driver, keys: Union[Sequence[str], Mapping[str, str]],
                  tile_x: int, tile_y: int, tile_z: int, *,
                  tilesize: Sequence[int] = (256, 256)) -> np.ndarray:
    """Retrieve xyz tile data from given driver"""
    metadata = driver.get_metadata(keys)
    wgs_bounds = metadata['bounds']
    if not tile_exists(wgs_bounds, tile_x, tile_y, tile_z):
        raise exceptions.TileOutOfBoundsError(
            f'Tile {tile_z}/{tile_x}/{tile_y} is outside image bounds'
        )
    target_bounds = get_xy_bounds(tile_x, tile_y, tile_z)
    return driver.get_raster_tile(keys, bounds=target_bounds, tilesize=tilesize)


def get_xy_bounds(tile_x: int, tile_y: int, tile_z: int) -> Tuple[float]:
    """Retrieve physical bounds covered by given xyz tile."""
    mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
    return mercantile.xy_bounds(mercator_tile)


def tile_exists(bounds: Sequence[float], tile_x: int, tile_y: int, tile_z: int) -> bool:
    """Check if a mercatile tile is inside a given bounds."""

    mintile = mercantile.tile(bounds[0], bounds[3], tile_z)
    maxtile = mercantile.tile(bounds[2], bounds[1], tile_z)

    return mintile.x <= tile_x <= maxtile.x + 1 and mintile.y <= tile_y <= maxtile.y + 1
