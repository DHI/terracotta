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

    def get_tile(band_key: str, stretch_override: Optional[Tuple[Number, Number]]) -> np.ndarray:
        keys = (*some_keys, band_key)

        with driver.connect():
            metadata = driver.get_metadata(keys)
            tile_data = xyz.get_tile_data(driver, keys, tile_x=tile_x, tile_y=tile_y,
                                          tile_z=tile_z, tilesize=tile_size)

        valid_mask = image.get_valid_mask(tile_data, nodata=metadata['nodata'])
        stretch_range = list(metadata['range'])

        if stretch_override is not None:
            scale_min, scale_max = stretch_override
            if scale_min is not None:
                stretch_range[0] = scale_min
            if scale_max is not None:
                stretch_range[1] = scale_max

        if stretch_range[1] < stretch_range[0]:
            raise exceptions.InvalidArgumentsError('Upper stretch bound must be higher than '
                                                   'lower bound')

        return image.to_uint8(tile_data, *stretch_range), valid_mask

    with concurrent.futures.ThreadPoolExecutor(3) as executor:
        results = executor.map(get_tile, rgb_values, stretch_ranges_)
        for i, (band_data, band_valid_mask) in enumerate(results):
            out[..., i] = band_data
            valid_mask &= band_valid_mask

    return image.array_to_png(out, transparency_mask=~valid_mask)
