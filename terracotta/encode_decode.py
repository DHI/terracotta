import numpy as np
from PIL import Image


def array_to_img(arr):
    """Convert Numpy array to png img.
    Only single-band uin8 data supported for now."""

    arr = np.asarray(arr, dtype=np.uint8)
    assert arr.ndim == 2
    img = Image.fromarray(arr, mode='L')
    return img
