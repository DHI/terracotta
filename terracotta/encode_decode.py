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
