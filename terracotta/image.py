from typing import Optional, Sequence, Tuple, Mapping, Any, TypeVar
from typing.io import BinaryIO
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
    lower_bound_in, upper_bound_in = in_range
    lower_bound_out, upper_bound_out = out_range
    out_data = data.astype('float64', copy=True)
    out_data -= lower_bound_in
    out_data *= (upper_bound_out - lower_bound_out) / (upper_bound_in - lower_bound_in)
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
    import matplotlib.cm

    cmap_ = cmap or 'Greys_r'
    try:
        mapper = matplotlib.cm.get_cmap(cmap_)
    except ValueError as e:
        raise exceptions.InvalidArgumentsError('Encountered invalid colormap') from e

    return mapper(contrast_stretch(data, data_range, (0, 1)))


def get_stretch_range(method: str, metadata: Mapping[str, Any],
                      data_range: Sequence[Number] = None,
                      percentiles: Sequence[Number] = None) -> Tuple[Number, Number]:
    global_min, global_max = metadata['range']

    if method == 'stretch':
        data_min, data_max = data_range or (None, None)
        stretch_range = (data_min or global_min, data_max or global_max)

    elif method == 'histogram_cut':
        stretch_percentile = percentiles or (2, 98)
        if len(stretch_percentile) != 2:
            raise ValueError('Need exactly two percentiles')
        image_percentiles = np.concatenate(
            ([global_min], metadata['percentiles'], [global_max])
        )
        interpolated_percentiles = np.interp(stretch_percentile, np.arange(0, 101),
                                             image_percentiles)
        stretch_range = (interpolated_percentiles[0], interpolated_percentiles[1])

    else:
        raise exceptions.InvalidArgumentsError(f'unrecognized stretching method {method}')

    return stretch_range
