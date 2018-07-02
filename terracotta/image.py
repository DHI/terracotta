from io import BytesIO

import numpy as np
from PIL import Image

BAND_TO_MODE = {
    1: 'L',
    2: 'LA',
    3: 'RGB',
    4: 'RGBA'
}


def array_to_img(arr, alpha_mask=None):
    """Convert Numpy array to img.
    input array can be shape (H,W), (H,W,2), (H,W,3) or (H,W,4).
    Will be interpreted as L, LA, RGB and RGBA respectively.
    Parameters
    ----------
    arr: numpy array
        Image data.
    alpha_mask: numpy array
        Alpha values (0 transparent, 255 opaque).
        If input shape is (H,W,2) or (H,W,4) and alpha_mask is None,
        the last slice will be used as alpha.
    Returns
    -------
    out: PIL Image
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


def array_to_png(arr, alpha_mask=None):
    img = array_to_img(arr, alpha_mask=alpha_mask)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=0)
    sio.seek(0)
    return sio


def get_alpha_mask(data, nodata):
    """Return alpha layer for tile, where nodata NaNs and Infs are transparent.

    Parameters
    ----------
    tile: np.array
        The image tile.
    ds_name: string
        Internal name of the dataset.
    tilesize: int
        length of one side of tile

    Returns
    -------
    out: np.array of uint8
        Array of alpha values"""

    if data.ndim not in (2, 3):
        raise ValueError('Encountered invalid shape (must be 2 or 3-dimensional)')

    if data.ndim == 2:
        data = data[..., np.newaxis]

    nodata = list(nodata)
    if len(nodata) != data.shape[-1]:
        raise ValueError('Need one nodata value per data band')

    out_shape = data.shape[:-1]
    alpha_mask = np.full(out_shape, 255, np.uint8)

    for band, nodata_value in enumerate(nodata):
        alpha_mask[data[..., band] == nodata_value] = 0

    # Also mask out other invalid values if float
    if np.issubdtype(data.dtype, np.floating):
        alpha_mask[np.any(~np.isfinite(data), axis=-1)] = 0

    return alpha_mask


def contrast_stretch(data, in_range, out_range, clip=True):
    lower_bound_in, upper_bound_in = in_range
    lower_bound_out, upper_bound_out = out_range
    out_data = data - lower_bound_in
    out_data *= (upper_bound_out - lower_bound_out) / (upper_bound_in - lower_bound_in)
    out_data += lower_bound_out
    if clip:
        np.clip(out_data, *out_range, out=out_data)
    return out_data


def to_uint8(data, lower_bound, upper_bound):
    """Re-scale an array to [0, 255].

    Parameters
    ----------
    lower_bound, upper_bound: number
        Upper and lower bound of input data for stretch

    Returns
    -------
    out: ndarray
        Input data as uint8, scaled to [0, 255]
    """
    rescaled = contrast_stretch(data, (lower_bound, upper_bound), (0, 255), clip=True)
    return rescaled.astype(np.uint8)


def img_cmap(tile, data_range, cmap='inferno'):
    """Maps input tile data to colormap.

    Parameters
    ----------
    tile: numpy array
        2d array of tile data
    data_range: (number, number)
        (min, max) values to map from data to cmap.
        tile values outside will be clamped to cmap min or max.
    cmap: str
        Name of matplotlib colormap to use.
        https://matplotlib.org/examples/color/colormaps_reference.html

    Returns
    -------
    out: numpy array
        Numpy RGBA array

    """
    import matplotlib.cm
    try:
        mapper = matplotlib.cm.get_cmap(cmap)
    except ValueError as e:
        raise ValueError('Encountered invalid colormap') from e

    return mapper(contrast_stretch(tile, data_range, (0, 1)))


def get_stretch_range(method, metadata, data_min=None, data_max=None, percentiles=None):
    if method == 'stretch':
        stretch_range = (data_min or metadata['min'], data_max or metadata['max'])
    elif method == 'histogram_cut':
        stretch_percentile = percentiles or (2, 98)
        image_percentiles = np.concatenate(
            (metadata['min'], metadata['percentiles'], metadata['max'])
        )
        stretch_range = np.interp(stretch_percentile, np.arange(0, 101), image_percentiles)
    else:
        raise ValueError(f'unrecognized stretching method {method}')

    return stretch_range
