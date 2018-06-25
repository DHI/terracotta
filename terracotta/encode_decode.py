import numpy as np
import matplotlib
import matplotlib.cm as cm
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


def contrast_stretch(tile, val_range):
    """Scale an image to between 0 and 255.

    Parameters
    ----------
    val_range: (int, int)
        min and max value of input tile

    Returns
    -------
    out: numpy array
        input tile scaled to 0 - 255.
    """

    _, max_val = val_range
    if max_val == 0:
        tile[:] = 0
    else:
        tile *= 255 // max_val
    tile = tile.astype(np.uint8)
    return tile


def img_cmap(tile, range, cmap='inferno'):
    """Maps input tile data to colormap.

    Parameters
    ----------
    tile: numpy array
        2d array of tile data
    range: tuple of len(2)
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

    normalizer = matplotlib.colors.Normalize(vmin=range[0], vmax=range[1], clip=True)
    try:
        mapper = cm.ScalarMappable(norm=normalizer, cmap=cmap)
    except ValueError as e:
        raise ValueError('Possibly invalid colormap') from e

    rgba = mapper.to_rgba(tile, bytes=True, norm=True)

    return rgba
