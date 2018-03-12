import numpy as np
from PIL import Image


def array_to_img(arr, alpha_mask):
    """Convert Numpy array to png img.
    Only single-band uin8 data supported for now."""

    assert arr.ndim == 2

    arr = arr.astype(np.uint8)
    alpha_mask = alpha_mask.astype(np.uint16)

    # High byte is alpha, low is greyscale val
    alpha_mask <<= 8
    alpha_mask += arr

    img = Image.fromarray(alpha_mask, mode='LA')

    return img
