from PIL import Image
import numpy as np
import rasterio
import rasterio.vrt
import mercantile

import pytest


def test_singleband_handler(read_only_database, monkeypatch, raster_file):
    import terracotta
    settings = terracotta.config.parse_config({'DRIVER_PATH': str(read_only_database)})
    monkeypatch.setattr(terracotta, 'get_settings', lambda: settings)

    with rasterio.open(str(raster_file)) as src:
        with rasterio.vrt.WarpedVRT(src, crs='epsg:4326') as vrt:
            raster_bounds = vrt.bounds

    tile = mercantile.tile(raster_bounds[0], raster_bounds[3], 10)
    xyz = (tile.x, tile.y, 10)

    from terracotta.handlers import datasets, singleband
    ds = datasets.datasets()

    for keys in ds:
        raw_img = singleband.singleband(keys, xyz)
        img_data = np.asarray(Image.open(raw_img))
        assert img_data.shape == (*settings.TILE_SIZE, 2)


def test_singleband_out_of_bounds(read_only_database, monkeypatch, raster_file):
    import terracotta
    settings = terracotta.config.parse_config({'DRIVER_PATH': str(read_only_database)})
    monkeypatch.setattr(terracotta, 'get_settings', lambda: settings)

    from terracotta.handlers import datasets, singleband
    ds = datasets.datasets()

    for keys in ds:
        with pytest.raises(terracotta.exceptions.TileOutOfBoundsError):
            singleband.singleband(keys, (10, 0, 0))
