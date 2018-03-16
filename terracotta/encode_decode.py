import numpy as np
import matplotlib
import matplotlib.cm as cm
from PIL import Image


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
    out: PIL Image"""

    if not arr.ndim > 1 and arr.ndim < 4:
        raise ValueError("Img must have 2 or 3 dimensions")
    if arr.ndim == 2:
        # Make a new dimension for alpha mask
        arr = arr[:, :, np.newaxis]
    elif arr.ndim == 3 and arr.shape[2] > 4:
        raise ValueError("Check array shape, only L, LA, RGB and RGBA supported")
    if alpha_mask is None:
        if arr.shape[2] == 2 or arr.shape[2] == 4:
            # Assume last slice is alpha
            alpha_mask = None
        else:
            alpha_mask = np.full((arr.shape[0], arr.shape[1]), 255, dtype=np.uint8)

    if arr.shape[2] == 1 or arr.shape[2] == 3:
        arr = np.dstack((arr, alpha_mask))
    else:
        if alpha_mask is not None:
            arr[:, :, -1] = alpha_mask

    if arr.shape[2] == 2:
        img = Image.fromarray(arr, mode='LA')
    elif arr.shape[2] == 4:
        img = Image.fromarray(arr, mode='RGBA')
    else:
        raise ValueError("Unreachable code")

    return img


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
    mapper = cm.ScalarMappable(norm=normalizer, cmap=cmap)

    rgba = mapper.to_rgba(tile, bytes=True, norm=True)

    return rgba
