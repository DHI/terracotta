"""image.py

Utilities to create and manipulate images.
"""

from typing import Optional, Sequence, Tuple, TypeVar
from typing.io import BinaryIO
import warnings
from io import BytesIO

import numpy as np
from PIL import Image

from terracotta import exceptions

BAND_TO_MODE = {
    1: 'L',
    2: 'LA',
    3: 'RGB',
    4: 'RGBA'
}

Number = TypeVar('Number', int, float)


def array_to_img(arr: np.ndarray, alpha_mask: Optional[np.ndarray] = None) -> Image:
    """Convert NumPy array to PIL Image.

    Input array can be shape (H,W), (H,W,2), (H,W,3) or (H,W,4).
    Will be interpreted as L, LA, RGB and RGBA respectively.
    """
    if arr.ndim not in [2, 3]:
        raise ValueError("Img must have 2 or 3 dimensions")

    if arr.ndim == 2:
        # Make a new dimension for alpha mask
        arr = arr[:, :, np.newaxis]

    num_bands = arr.shape[2]

    if 1 > num_bands > 4:
        raise ValueError("Check array shape, only L, LA, RGB and RGBA supported")

    if alpha_mask is not None:
        if num_bands in [2, 4]:  # assume last slice is alpha
            arr[:, :, -1] = alpha_mask
        else:
            arr = np.dstack((arr, alpha_mask))

    return Image.fromarray(arr, mode=BAND_TO_MODE[arr.shape[2]])


def array_to_png(arr: np.ndarray, alpha_mask: Optional[np.ndarray] = None) -> BinaryIO:
    img = array_to_img(arr, alpha_mask=alpha_mask)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=0)
    sio.seek(0)
    return sio


def empty_image(size: Tuple[int, int]) -> BinaryIO:
    img = np.zeros(size, dtype='uint8')
    return array_to_png(img, alpha_mask=img)


def get_valid_mask(data: np.ndarray, nodata: Number) -> np.ndarray:
    """Return mask for data, masking out nodata and invalid values"""
    out = data != nodata

    # Also mask out other invalid values if float
    if np.issubdtype(data.dtype, np.floating):
        out &= np.isfinite(data)

    return out


def contrast_stretch(data: np.ndarray, in_range: Sequence[Number],
                     out_range: Sequence[Number], clip: bool = True) -> np.ndarray:
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
    """Re-scale an array to [0, 255] and cast to uint8"""
    rescaled = contrast_stretch(data, (lower_bound, upper_bound), (0, 255), clip=True)
    return rescaled.astype(np.uint8)


def apply_cmap(data: np.ndarray, data_range: Sequence[Number], cmap: str = None) -> np.ndarray:
    """Maps input data to colormap."""
    from terracotta.cmaps import get_cmap

    normalized_data = contrast_stretch(data, data_range, (0, 1))
    cmap_ = cmap or 'Greys_r'

    try:
        cmap_vals = get_cmap(cmap_)
    except ValueError as exc:
        raise exceptions.InvalidArgumentsError(f'Encountered invalid color map {cmap_}') from exc

    num_vals = cmap_vals.shape[0]

    # do linear interpolation
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', 'invalid value encountered.*', RuntimeWarning)
        idx = normalized_data * num_vals
        idx_floor = np.minimum(num_vals - 2, np.floor(idx).astype(np.int))
        idx_ceil = idx_floor + 1
        return (cmap_vals[idx_floor] + (idx - idx_floor)[..., np.newaxis]
                * (cmap_vals[idx_ceil] - cmap_vals[idx_floor]))
