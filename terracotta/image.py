"""image.py

Utilities to create and manipulate images.
"""

from typing import Sequence, Tuple, TypeVar, Union
from typing.io import BinaryIO

from io import BytesIO

import numpy as np
from PIL import Image

from terracotta.profile import trace
from terracotta import exceptions, get_settings

Number = TypeVar('Number', int, float)
RGBA = Tuple[Number, Number, Number, Number]
Palette = Sequence[RGBA]


@trace('array_to_png')
def array_to_png(img_data: Union[np.ndarray, np.ma.MaskedArray],
                 colormap: Union[str, Palette, None] = None) -> BinaryIO:
    from terracotta.cmaps import get_cmap

    transparency: Union[Tuple[int, int, int], int, bytes]

    settings = get_settings()
    compress_level = settings.PNG_COMPRESS_LEVEL

    if img_data.ndim == 3:  # encode RGB image
        if img_data.shape[-1] != 3:
            raise ValueError('3D input arrays must have three bands')

        if colormap is not None:
            raise ValueError('Colormap argument cannot be given for multi-band data')

        mode = 'RGB'
        transparency = (0, 0, 0)
        palette = None

    elif img_data.ndim == 2:  # encode paletted image
        mode = 'L'

        if colormap is None:
            palette = None
            transparency = 0
        else:
            if isinstance(colormap, str):
                # get and apply colormap by name
                try:
                    cmap_vals = get_cmap(colormap)
                except ValueError as exc:
                    raise exceptions.InvalidArgumentsError(
                        f'Encountered invalid color map {colormap}') from exc

                palette = np.concatenate((
                    np.zeros(3, dtype='uint8'),
                    cmap_vals.flatten()
                ))
                transparency = 0
            else:
                # explicit mapping
                if len(colormap) > 255:
                    raise exceptions.InvalidArgumentsError(
                        'Explicit color map must contain less than 256 values'
                    )

                colormap_array = np.asarray(colormap, dtype='uint8')
                if colormap_array.ndim != 2 or colormap_array.shape[1] != 4:
                    raise ValueError('Explicit color mapping must have shape (n, 4)')

                rgb, alpha = colormap_array[:, :-1], colormap_array[:, -1]
                palette = np.concatenate((
                    np.zeros(3, dtype='uint8'),
                    rgb.flatten(),
                    np.zeros(3 * (256 - len(colormap) - 1), dtype='uint8')
                ))
                transparency = np.concatenate((
                    [0], alpha, np.zeros(256 - len(colormap) - 1, dtype='uint8')
                )).tobytes()

            assert palette.shape == (3 * 256,), palette.shape

    if isinstance(img_data, np.ma.MaskedArray):
        img_data = img_data.filled(0)

    img = Image.fromarray(img_data, mode=mode)

    if palette is not None:
        img.putpalette(palette)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=compress_level, transparency=transparency)
    sio.seek(0)
    return sio


def empty_image(size: Tuple[int, int]) -> BinaryIO:
    """Return a fully transparent PNG image of given size"""
    settings = get_settings()
    compress_level = settings.PNG_COMPRESS_LEVEL

    img = Image.new(mode='P', size=size, color=0)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=compress_level, transparency=0)
    sio.seek(0)
    return sio


@trace('contrast_stretch')
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

    out_data = data.astype('float64').copy()
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


def label(data: np.ndarray, labels: Sequence[Number]) -> np.ndarray:
    """Create a labelled uint8 version of data, with output values starting at 1.

    Values not found in labels are replaced by 0.

    Example:

        >>> data = np.array([15, 16, 17])
        >>> label(data, [17, 15])
        np.array([2, 0, 1])

    """
    if len(labels) > 255:
        raise ValueError('Cannot fit more than 255 labels')

    out_data = np.zeros(data.shape, dtype='uint8')
    for i, label in enumerate(labels, 1):
        out_data[data == label] = i

    return out_data
