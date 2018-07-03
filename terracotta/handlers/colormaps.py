from typing import List


def colormaps() -> List[str]:
    """Return all supported colormaps"""
    from matplotlib.cm import cmap_d
    return cmap_d
