import numpy as np
import matplotlib as mpl
import matplotlib.cm

ALL_MAPS = mpl.cm.datad


def generate_maps(num_vals):
    x = np.linspace(0, 1, num_vals)
    for cmap in ALL_MAPS:
        cmap_fun = mpl.cm.get_cmap(cmap)
        cmap_vals = cmap_fun(x)
        np.savetxt(f'{cmap}_rgb.txt', cmap_vals)


if __name__ == '__main__':
    import sys
    num_vals = sys.argv[1] if len(sys.argv) > 1 else 255
    generate_maps(num_vals=num_vals)
