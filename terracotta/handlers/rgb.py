import concurrent.futures
from typing import Sequence, Mapping, Any
from typing.io import BinaryIO

from terracotta.drivers.base import Driver
from terracotta import settings, image, xyz


def rgb(driver: Driver, some_keys: Mapping[str, str], tile_xyz: Sequence[int],
        rgb_values: Sequence[str], *, stretch_method: str = 'stretch',
        stretch_options: Mapping[str, Any] = None) -> BinaryIO:
    """Return RGB image as PNG

    Red, green, and blue channels correspond to the given values `rgb_values` of the key
    missing from `some_keys`.
    """
    import numpy as np

    stretch_options = stretch_options or {}

    if len(rgb_values) != 3:
        raise ValueError('rgb_values argument must contain three values')

    try:
        tile_x, tile_y, tile_z = tile_xyz
    except ValueError:
        raise ValueError('xyz argument must contain three values')

    with driver.connect():
        available_keys = driver.available_keys
        unspecified_key = set(some_keys.keys()) - set(available_keys)

        if len(unspecified_key) != 1:
            raise ValueError('some_keys argument must specify all keys except one')

        unspecified_key = unspecified_key[0]
        band_keys = [dict(some_keys, {unspecified_key: band_key}) for band_key in rgb_values]
        metadata = [driver.get_metadata(band_key) for band_key in band_keys]

        tile_size = settings.TILE_SIZE
        out = np.empty(tile_size + (3,), dtype='uint8')
        valid_mask = np.ones(tile_size, dtype='bool')

        def get_tile(keys, metadata):
            tile_data = xyz.get_tile_data(driver, keys, tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                          tilesize=tile_size)
            valid_mask = image.get_valid_mask(out, nodata=metadata['nodata'])
            stretch_range = image.get_stretch_range(stretch_method, metadata, **stretch_options)
            return image.to_uint8(tile_data, *stretch_range), valid_mask

        with concurrent.futures.ThreadPoolExecutor(3) as executor:
            results = executor.map(get_tile, band_keys, metadata)
            for i, (band_data, band_valid_mask) in enumerate(results):
                out[..., i] = band_data
                valid_mask &= band_valid_mask

    alpha_mask = (255 * valid_mask).astype('uint8')
    return image.array_to_png(out, alpha_mask=alpha_mask)
