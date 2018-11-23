"""handlers/rgb.py

Handle /rgb API endpoint. Band file retrieval is multi-threaded.
"""

from typing import Sequence, Tuple, Optional, TypeVar
from typing.io import BinaryIO
from concurrent.futures import Future

from terracotta import get_settings, get_driver, image, xyz, exceptions
from terracotta.profile import trace

Number = TypeVar('Number', int, float)
ListOfRanges = Sequence[Optional[Tuple[Optional[Number], Optional[Number]]]]


@trace('rgb_handler')
def rgb(some_keys: Sequence[str],
        rgb_values: Sequence[str],
        tile_xyz: Tuple[int, int, int] = None, *,
        stretch_ranges: ListOfRanges = None,
        tile_size: Tuple[int, int] = None) -> BinaryIO:
    """Return RGB image as PNG

    Red, green, and blue channels correspond to the given values `rgb_values` of the key
    missing from `some_keys`.
    """
    import numpy as np

    # make sure all stretch ranges contain two values
    if stretch_ranges is None:
        stretch_ranges = [None, None, None]

    if len(stretch_ranges) != 3:
        raise exceptions.InvalidArgumentsError('stretch_ranges argument must contain 3 values')

    stretch_ranges_ = [stretch_range or (None, None) for stretch_range in stretch_ranges]

    if len(rgb_values) != 3:
        raise exceptions.InvalidArgumentsError('rgb_values argument must contain 3 values')

    settings = get_settings()

    if tile_size is None:
        tile_size_ = settings.DEFAULT_TILE_SIZE
    else:
        tile_size_ = tile_size

    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    with driver.connect():
        key_names = driver.key_names

        if len(some_keys) != len(key_names) - 1:
            raise exceptions.InvalidArgumentsError('must specify all keys except last one')

        def get_band_future(band_key: str) -> Future:
            band_keys = (*some_keys, band_key)
            return xyz.get_tile_data(driver, band_keys, tile_xyz=tile_xyz,
                                     tile_size=tile_size_, asynchronous=True)

        futures = [get_band_future(key) for key in rgb_values]
        band_items = zip(rgb_values, stretch_ranges_, futures)

        out_arrays = []

        for i, (band_key, band_stretch_override, band_data_future) in enumerate(band_items):
            keys = (*some_keys, band_key)
            metadata = driver.get_metadata(keys)

            band_stretch_range = list(metadata['range'])
            scale_min, scale_max = band_stretch_override

            if scale_min is not None:
                band_stretch_range[0] = scale_min

            if scale_max is not None:
                band_stretch_range[1] = scale_max

            if band_stretch_range[1] < band_stretch_range[0]:
                raise exceptions.InvalidArgumentsError(
                    'Upper stretch bound must be higher than lower bound'
                )

            band_data = band_data_future.result()
            out_arrays.append(image.to_uint8(band_data, *band_stretch_range))

    out = np.ma.stack(out_arrays, axis=-1)
    return image.array_to_png(out)
