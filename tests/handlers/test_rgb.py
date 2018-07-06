from PIL import Image
import numpy as np
import rasterio
import rasterio.vrt
import mercantile

import pytest


def test_rgb_handler(use_read_only_database, raster_file):
    import terracotta

    with rasterio.open(str(raster_file)) as src:
        with rasterio.vrt.WarpedVRT(src, crs='epsg:4326') as vrt:
            raster_bounds = vrt.bounds

    tile = mercantile.tile(raster_bounds[0], raster_bounds[3], 10)
    xyz = (tile.x, tile.y, 10)

    from terracotta.handlers import rgb
    raw_img = rgb.rgb(['val21'], xyz, ['val22', 'val23', 'val24'])
    img_data = np.asarray(Image.open(raw_img))
    assert img_data.shape == (*terracotta.get_settings().TILE_SIZE, 4)


def test_rgb_out_of_bounds(use_read_only_database, raster_file):
    import terracotta
    from terracotta.handlers import rgb

    with pytest.raises(terracotta.exceptions.TileOutOfBoundsError):
        rgb.rgb(['val21'], (10, 0, 0), ['val22', 'val23', 'val24'])
