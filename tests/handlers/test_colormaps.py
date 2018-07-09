
def test_colormaps():
    from terracotta.handlers import colormaps
    assert colormaps.colormaps()

    from matplotlib.cm import cmap_d
    assert all(cmap.lower() in colormaps.colormaps() for cmap in cmap_d)
