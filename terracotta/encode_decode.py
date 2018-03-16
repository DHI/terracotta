import numpy as np
from PIL import Image


def array_to_img(arr, alpha_mask):
    """Convert Numpy array to png img.
    Only single-band uint8 data supported for now.

    Parameters
    ----------
    arr: numpy array
        Image greyscale data.
    alpha_mask: numpy array
        Alpha values (0 transparent, 255 opaque).

    Returns
    -------
    out: PIL Image
        greyscale with alpha image"""

    assert arr.ndim == 2

    arr = arr.astype(np.uint8)
    alpha_mask = alpha_mask.astype(np.uint16)

    # High byte is alpha, low is greyscale val
    alpha_mask <<= 8
    alpha_mask += arr

    img = Image.fromarray(alpha_mask, mode='LA')

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
