"""handlers/compute.py

Handle /compute API endpoint. Band file retrieval is multi-threaded.
"""

from typing import Sequence, Tuple, Mapping, Optional, TypeVar
from typing.io import BinaryIO
from concurrent.futures import Future

from terracotta import get_settings, get_driver, image, xyz, exceptions
from terracotta.profile import trace

Number = TypeVar('Number', int, float)
RangeType = Optional[Tuple[Optional[Number], Optional[Number]]]


@trace('compute_handler')
def compute(expression: str,
            some_keys: Sequence[str],
            operand_keys: Mapping[str, str],
            stretch_range: Tuple[Number, Number],
            tile_xyz: Tuple[int, int, int] = None, *,
            colormap: str = None,
            tile_size: Tuple[int, int] = None) -> BinaryIO:
    """Return singleband image computed from one or more images as PNG

    Expects a Python expression that returns a NumPy array. Operands in
    the expression are replaced by the images with keys as defined by
    some_keys (all but the last key) and operand_keys (last key).

    Contrary to singleband and rgb handlers, stretch_range must be given.

    Example:

        >>> operands = {
        ...     'v1': 'B08',
        ...     'v2': 'B04'
        ... }
        >>> compute('v1 * v2', ['S2', '20171101'], operands, [0, 1000])
        <binary image containing product of bands 4 and 8>

    """
    from terracotta.expressions import evaluate_expression

    if not stretch_range[1] > stretch_range[0]:
        raise exceptions.InvalidArgumentsError(
            'Upper stretch bounds must be larger than lower bounds'
        )

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

        futures = {var: get_band_future(key) for var, key in operand_keys.items()}
        operand_data = {var: future.result() for var, future in futures.items()}

    try:
        out = evaluate_expression(expression, operand_data)
    except ValueError as exc:
        # make sure error message gets propagated
        raise exceptions.InvalidArgumentsError(f'error while executing expression: {exc!s}')

    out = image.to_uint8(
        out,
        *stretch_range
    )
    return image.array_to_png(out, colormap=colormap)
