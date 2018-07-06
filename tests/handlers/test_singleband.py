from PIL import Image
import numpy as np

import pytest


def test_singleband_handler(use_read_only_database, raster_file, raster_file_xyz):
    import terracotta
    from terracotta.handlers import datasets, singleband
    settings = terracotta.get_settings()
    ds = datasets.datasets()

    for keys in ds:
        raw_img = singleband.singleband(keys, raster_file_xyz)
        img_data = np.asarray(Image.open(raw_img))
        assert img_data.shape == (*settings.TILE_SIZE, 2)


def test_singleband_out_of_bounds(use_read_only_database, raster_file):
    import terracotta
    from terracotta.handlers import datasets, singleband
    ds = datasets.datasets()

    for keys in ds:
        with pytest.raises(terracotta.exceptions.TileOutOfBoundsError):
            singleband.singleband(keys, (10, 0, 0))
