"""image.py

Utilities to create and manipulate images.
"""

from typing import Sequence, Tuple, TypeVar, Union
from typing.io import BinaryIO
from io import BytesIO

import numpy as np
from PIL import Image

from terracotta import exceptions

Number = TypeVar('Number', int, float)


def array_to_png(arr: np.ndarray,
                 transparency_mask: np.ndarray = None,
                 colormap: str = None) -> BinaryIO:
    from terracotta.cmaps import get_cmap

    transparency: Union[Tuple[int, int, int], int]

    if arr.ndim == 3:  # encode RGB image
        if arr.shape[-1] != 3:
            raise ValueError('3D input arrays must have three bands')

        if colormap is not None:
            raise ValueError('Colormap argument cannot be given for multi-band data')

        mode = 'RGB'
        transparency = (0, 0, 0)
        palette = None

    elif arr.ndim == 2:  # encode paletted image
        mode = 'L'
        transparency = 0

        if colormap is not None:
            try:
                cmap_vals = get_cmap(colormap)
            except ValueError as exc:
                raise exceptions.InvalidArgumentsError(
                    f'Encountered invalid color map {colormap}') from exc

            palette = np.concatenate((
                np.zeros(3, dtype='uint8'),
                cmap_vals.flatten()
            ))
            assert palette.shape == (3 * 256,)
        else:
            palette = None

    if transparency_mask is not None:
        if transparency_mask.ndim != 2 or transparency_mask.dtype != np.bool:
            raise ValueError('Alpha mask has to be a 2D boolean array')

        arr[transparency_mask, ...] = 0

    img = Image.fromarray(arr, mode=mode)

    if palette is not None:
        img.putpalette(palette)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=1, transparency=transparency)
    sio.seek(0)
    return sio


def empty_image(size: Tuple[int, int]) -> BinaryIO:
    img = Image.new(mode='P', size=size, color=0)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=1, transparency=0)
    sio.seek(0)
    return sio


def get_valid_mask(data: np.ndarray, nodata: Number) -> np.ndarray:
    """Return mask for data, masking out nodata and invalid values"""
    out = data != nodata

    # Also mask out other invalid values if float
    if np.issubdtype(data.dtype, np.floating):
        out &= np.isfinite(data)

    return out


def contrast_stretch(data: np.ndarray,
                     in_range: Sequence[Number],
                     out_range: Sequence[Number],
                     clip: bool = True) -> np.ndarray:
    """Normalize input array from in_range to out_range"""
    lower_bound_in, upper_bound_in = in_range
    lower_bound_out, upper_bound_out = out_range

    norm = upper_bound_in - lower_bound_in
    if abs(norm) < 1e-8:  # prevent division by zero
        return np.full(data.shape, lower_bound_out, dtype='float64')

    out_data = data.astype('float64', copy=True)
    out_data -= lower_bound_in
    out_data *= (upper_bound_out - lower_bound_out) / norm
    out_data += lower_bound_out

    if clip:
        np.clip(out_data, *out_range, out=out_data)

    return out_data


def to_uint8(data: np.ndarray, lower_bound: Number, upper_bound: Number) -> np.ndarray:
    """Re-scale an array to [1, 255] and cast to uint8 (0 is used for transparency)"""
    rescaled = contrast_stretch(data, (lower_bound, upper_bound), (1, 255), clip=True)
    return rescaled.astype(np.uint8)
