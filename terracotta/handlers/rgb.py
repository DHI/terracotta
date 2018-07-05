import concurrent.futures
from typing import Sequence, Mapping, Any, Tuple, Optional, TypeVar
from typing.io import BinaryIO

from terracotta import settings, get_driver, image, xyz, exceptions

Number = TypeVar('Number', int, float)


def rgb(some_keys: Sequence[str], tile_xyz: Sequence[int],
        rgb_values: Sequence[str], *, stretch_method: str = 'stretch',
        stretch_options: Mapping[str, Any] = None) -> BinaryIO:
    """Return RGB image as PNG

    Red, green, and blue channels correspond to the given values `rgb_values` of the key
    missing from `some_keys`.
    """
    import numpy as np

    _stretch_options = stretch_options or {}

    scale_ranges = []
    for k in ('r', 'g', 'b'):
        band_range = _stretch_options.get(f'{k}_range')
        if band_range and len(band_range) != 2:
            raise exceptions.InvalidArgumentsError(f'{k}_range argument must contain 2 values')
        scale_ranges.append(band_range)

    percentiles = _stretch_options.get('percentiles')
    if percentiles and len(percentiles) != 2:
        raise exceptions.InvalidArgumentsError('percentiles argument must contain 2 values')

    if len(rgb_values) != 3:
        raise exceptions.InvalidArgumentsError('rgb_values argument must contain 3 values')

    try:
        tile_x, tile_y, tile_z = tile_xyz
    except ValueError:
        raise exceptions.InvalidArgumentsError('xyz argument must contain 3 values')

    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    available_keys = driver.available_keys

    if len(some_keys) != len(available_keys) - 1:
        raise exceptions.InvalidArgumentsError('must specify all keys except last one')

    tile_size = settings.TILE_SIZE
    out = np.empty(tile_size + (3,), dtype='uint8')
    valid_mask = np.ones(tile_size, dtype='bool')

    def get_tile(band_key: str, scale_range: Optional[Tuple[Number]]) -> np.ndarray:
        keys = (*some_keys, band_key)

        with driver.connect():
            metadata = driver.get_metadata(keys)
            tile_data = xyz.get_tile_data(driver, keys, tile_x=tile_x, tile_y=tile_y,
                                          tile_z=tile_z, tilesize=tile_size)
        valid_mask = image.get_valid_mask(tile_data, nodata=metadata['nodata'])
        stretch_range = image.get_stretch_range(
            stretch_method, metadata, data_range=scale_range, percentiles=percentiles
        )
        return image.to_uint8(tile_data, *stretch_range), valid_mask

    with concurrent.futures.ThreadPoolExecutor(3) as executor:
        results = executor.map(get_tile, rgb_values, scale_ranges)
        for i, (band_data, band_valid_mask) in enumerate(results):
            out[..., i] = band_data
            valid_mask &= band_valid_mask

    alpha_mask = image.to_uint8(valid_mask, 0, 1)
    return image.array_to_png(out, alpha_mask=alpha_mask)
