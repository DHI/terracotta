"""handlers/rgb.py

Handle /rgb API endpoint. Band file retrieval is multi-threaded.
"""

import concurrent.futures
from typing import Sequence, Tuple, Optional, TypeVar
from typing.io import BinaryIO

from terracotta import get_settings, get_driver, image, xyz, exceptions

Number = TypeVar('Number', int, float)
ListOfRanges = Sequence[Optional[Tuple[Optional[Number], Optional[Number]]]]


def rgb(some_keys: Sequence[str], tile_xyz: Sequence[int], rgb_values: Sequence[str], *,
        stretch_ranges: ListOfRanges = None) -> BinaryIO:
    """Return RGB image as PNG

    Red, green, and blue channels correspond to the given values `rgb_values` of the key
    missing from `some_keys`.
    """
    import numpy as np

    stretch_ranges_ = stretch_ranges or (None, None, None)

    if len(stretch_ranges_) != 3:
        raise exceptions.InvalidArgumentsError('stretch_ranges argument must contan 3 values')

    if len(rgb_values) != 3:
        raise exceptions.InvalidArgumentsError('rgb_values argument must contain 3 values')

    try:
        tile_x, tile_y, tile_z = tile_xyz
    except ValueError:
        raise exceptions.InvalidArgumentsError('xyz argument must contain 3 values')

    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    available_keys = driver.available_keys

    if len(some_keys) != len(available_keys) - 1:
        raise exceptions.InvalidArgumentsError('must specify all keys except last one')

    tile_size = settings.TILE_SIZE
    out = np.empty(tile_size + (3,), dtype='uint8')
    valid_mask = np.ones(tile_size, dtype='bool')

    def get_tile(band_key: str, scale_range: Optional[Tuple[Number, Number]]) -> np.ndarray:
        keys = (*some_keys, band_key)

        with driver.connect():
            metadata = driver.get_metadata(keys)
            tile_data = xyz.get_tile_data(driver, keys, tile_x=tile_x, tile_y=tile_y,
                                          tile_z=tile_z, tilesize=tile_size)

        valid_mask = image.get_valid_mask(tile_data, nodata=metadata['nodata'])
        global_min, global_max = metadata['range']
        if scale_range is not None:
            stretch_range = (scale_range[0] or global_min, scale_range[1] or global_max)
        else:
            stretch_range = (global_min, global_max)
        return image.to_uint8(tile_data, *stretch_range), valid_mask

    with concurrent.futures.ThreadPoolExecutor(3) as executor:
        results = executor.map(get_tile, rgb_values, stretch_ranges_)
        for i, (band_data, band_valid_mask) in enumerate(results):
            out[..., i] = band_data
            valid_mask &= band_valid_mask

    alpha_mask = image.to_uint8(valid_mask, 0, 1)
    return image.array_to_png(out, alpha_mask=alpha_mask)
