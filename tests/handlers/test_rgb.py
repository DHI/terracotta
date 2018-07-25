from PIL import Image
import numpy as np

import pytest


def test_rgb_handler(use_read_only_database, raster_file, raster_file_xyz):
    import terracotta
    from terracotta.handlers import rgb
    raw_img = rgb.rgb(['val21'], raster_file_xyz, ['val22', 'val23', 'val24'])
    img_data = np.asarray(Image.open(raw_img))
    assert img_data.shape == (*terracotta.get_settings().TILE_SIZE, 4)


def test_rgb_out_of_bounds(use_read_only_database, raster_file):
    import terracotta
    from terracotta.handlers import rgb

    with pytest.raises(terracotta.exceptions.TileOutOfBoundsError) as excinfo:
        rgb.rgb(['val21'], (10, 0, 0), ['val22', 'val23', 'val24'])
        assert 'data covers less than' not in str(excinfo.value)


def test_rgb_lowzoom(use_read_only_database, raster_file, raster_file_xyz_lowzoom):
    import terracotta
    from terracotta.handlers import rgb

    with pytest.raises(terracotta.exceptions.TileOutOfBoundsError) as excinfo:
        rgb.rgb(['val21'], raster_file_xyz_lowzoom, ['val22', 'val23', 'val24'])
        assert 'data covers less than' in str(excinfo.value)
