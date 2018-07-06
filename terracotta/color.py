import os

import numpy as np


CMAP_FOLDER = os.path.join(os.path.dirname(__file__), 'cmaps')
CMAP_SUFFIX = '_rgb.txt'
AVAILABLE_CMAPS = [f[:-len(CMAP_SUFFIX)] for f in os.listdir(CMAP_FOLDER)
                   if f.endswith(CMAP_SUFFIX)]


class Normalizer:
    def __init__(self, vmin=None, vmax=None, clip=False):
        self.vmin = vmin
        self.vmax = vmax
        self.clip = clip

    def __call__(self, arr):
        if self.vmin is None:
            self.vmin = np.nanmin(arr)
        if self.vmax is None:
            self.vmax = np.nanmax(arr)
        norm_vals = (arr - self.vmin) / (self.vmax - self.vmin)
        if self.clip:
            norm_vals = np.clip(arr, self.vmin, self.vmax)
        return norm_vals


def _get_cmap_values(cmap_name):
    cmap_path = os.path.join(CMAP_FOLDER, f'{cmap_name}_rgb.txt')
    assert os.path.isfile(cmap_path)
    return np.loadtxt(cmap_path)


def get_cmap(cmap_name):
    if cmap_name not in AVAILABLE_CMAPS:
        raise ValueError(f'Unknown color map {cmap_name}')

    cmap_vals = _get_cmap_values(cmap_name)
    num_vals = cmap_vals.shape[0]

    def cmap_interpolator(x):
        out = np.empty(x.shape + (4,))
        valid_values = np.logical_and(x >= 0, x <= 1)
        out[~valid_values] = np.nan

        valid_idx = x[valid_values] * num_vals
        idx_floor = np.minimum(num_vals - 1, np.floor(valid_idx).astype(np.int))
        idx_ceil = np.minimum(num_vals - 1, idx_floor + 1)
        out[valid_values] = cmap_vals[idx_floor] + (valid_idx - idx_floor)[:, np.newaxis] * (cmap_vals[idx_ceil] - cmap_vals[idx_floor])
        return out

    return cmap_interpolator
