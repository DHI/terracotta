"""cmaps/generate_cmaps.py

A script to generate color map dumps from matplotlib.
"""

import numpy as np
import matplotlib as mpl

from terracotta.cmaps.get_cmaps import SUFFIX

ALL_CMAPS = list(mpl.colormaps)
NUM_VALS = 255


def generate_maps(out_folder: str) -> None:
    x = np.linspace(0, 1, NUM_VALS)
    for cmap in ALL_CMAPS:
        print(cmap)
        cmap_fun = mpl.colormaps[cmap]
        cmap_vals = cmap_fun(x)
        cmap_uint8 = (cmap_vals * 255).astype("uint8")
        np.save(f"{out_folder}/{cmap.lower()}{SUFFIX}", cmap_uint8)


if __name__ == "__main__":
    import os

    here = os.path.dirname(os.path.realpath(__file__))
    out_folder = os.path.join(here, "data")
    generate_maps(out_folder=out_folder)
