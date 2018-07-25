"""cmaps/generate_cmaps.py

A script to generate color map dumps from matplotlib.
"""

import numpy as np
import matplotlib.cm as cm

from terracotta.cmaps import SUFFIX

ALL_MAPS = cm.cmap_d


def generate_maps(out_folder: str, num_vals: int = 255) -> None:
    x = np.linspace(0, 1, num_vals)
    for cmap in ALL_MAPS:
        cmap_fun = cm.get_cmap(cmap)
        cmap_vals = cmap_fun(x).astype('float32')
        np.save(f'{out_folder}/{cmap.lower()}{SUFFIX}', cmap_vals)


if __name__ == '__main__':
    import os
    import sys
    num_vals = sys.argv[1] if len(sys.argv) > 1 else 255
    here = os.path.dirname(__file__)
    generate_maps(num_vals=num_vals, out_folder=here)  # type: ignore
