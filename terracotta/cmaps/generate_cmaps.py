"""cmaps/generate_cmaps.py

A script to generate color map dumps from matplotlib.
"""

import numpy as np
import matplotlib.cm as cm

from terracotta.cmaps import SUFFIX

ALL_MAPS = cm.cmap_d
NUM_VALS = 255


def generate_maps(out_folder: str) -> None:
    x = np.linspace(0, 1, NUM_VALS)
    for cmap in ALL_MAPS:
        print(cmap)
        cmap_fun = cm.get_cmap(cmap)
        cmap_vals = cmap_fun(x)[:, :-1]  # cut off alpha
        cmap_uint8 = (cmap_vals * 255).astype('uint8')
        np.save(f'{out_folder}/{cmap.lower()}{SUFFIX}', cmap_uint8)


if __name__ == '__main__':
    import os
    here = os.path.dirname(os.path.realpath(__file__))
    generate_maps(out_folder=here)
