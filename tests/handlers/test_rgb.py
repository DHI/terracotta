from PIL import Image
import numpy as np

import pytest


def test_rgb_handler(use_testdb, raster_file, raster_file_xyz):
    import terracotta
    from terracotta.handlers import rgb
    raw_img = rgb.rgb(['val21', 'x'], ['val22', 'val23', 'val24'], raster_file_xyz)
    img_data = np.asarray(Image.open(raw_img))
    assert img_data.shape == (*terracotta.get_settings().DEFAULT_TILE_SIZE, 3)


def test_rgb_tile_size(use_testdb, raster_file, raster_file_xyz):
    from terracotta.handlers import rgb
    raw_img = rgb.rgb(['val21', 'x'], ['val22', 'val23', 'val24'], raster_file_xyz,
                      tile_size=(100, 100))
    img_data = np.asarray(Image.open(raw_img))
    assert img_data.shape == (100, 100, 3)


def test_rgb_invalid_keys(use_testdb, raster_file_xyz):
    from terracotta import exceptions
    from terracotta.handlers import rgb

    with pytest.raises(exceptions.InvalidArgumentsError):
        rgb.rgb(['val21', 'x', 'y', 'z'], ['val22', 'val23', 'val24'], raster_file_xyz)


def test_rgb_invalid_args(use_testdb, raster_file_xyz):
    from terracotta import exceptions
    from terracotta.handlers import rgb

    with pytest.raises(exceptions.InvalidArgumentsError):
        rgb.rgb(['val21', 'x'], ['val22', 'val23', 'val24'], raster_file_xyz, stretch_ranges=[])


def test_rgb_invalid_rgb_values(use_testdb, raster_file_xyz):
    from terracotta import exceptions
    from terracotta.handlers import rgb

    with pytest.raises(exceptions.InvalidArgumentsError):
        rgb.rgb(['val21', 'x'], ['val22', 'val23'], raster_file_xyz)


def test_rgb_out_of_bounds(use_testdb, raster_file):
    import terracotta
    from terracotta.handlers import rgb

    with pytest.raises(terracotta.exceptions.TileOutOfBoundsError) as excinfo:
        rgb.rgb(['val21', 'x'], ['val22', 'val23', 'val24'], (10, 0, 0))
        assert 'data covers less than' not in str(excinfo.value)


def test_rgb_lowzoom(use_testdb, raster_file, raster_file_xyz_lowzoom):
    import terracotta
    from terracotta.handlers import rgb

    with pytest.raises(terracotta.exceptions.TileOutOfBoundsError) as excinfo:
        rgb.rgb(['val21', 'x'], ['val22', 'val23', 'val24'], raster_file_xyz_lowzoom)
        assert 'data covers less than' in str(excinfo.value)


@pytest.mark.parametrize('stretch_range', [[0, 20000], [10000, 20000], [-50000, 50000], [100, 100]])
def test_rgb_stretch(stretch_range, use_testdb, testdb, raster_file_xyz):
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import rgb

    ds_keys = ['val21', 'x', 'val22']

    raw_img = rgb.rgb(ds_keys[:2], ['val22', 'val23', 'val24'], raster_file_xyz,
                      stretch_ranges=[stretch_range] * 3)
    img_data = np.asarray(Image.open(raw_img))[..., 0]

    # get unstretched data to compare to
    driver = terracotta.get_driver(testdb)

    with driver.connect():
        tile_data = get_tile_data(driver, ds_keys, tile_xyz=raster_file_xyz,
                                  tile_size=img_data.shape)

    # filter transparent values
    valid_mask = ~tile_data.mask
    assert np.all(img_data[~valid_mask] == 0)

    valid_img = img_data[valid_mask]
    valid_data = tile_data.compressed()

    assert np.all(valid_img[valid_data < stretch_range[0]] == 1)
    stretch_range_mask = (valid_data > stretch_range[0]) & (valid_data < stretch_range[1])
    assert np.all(valid_img[stretch_range_mask] >= 1)
    assert np.all(valid_img[stretch_range_mask] <= 255)
    assert np.all(valid_img[valid_data > stretch_range[1]] == 255)


def test_rgb_invalid_stretch(use_testdb, raster_file_xyz):
    from terracotta import exceptions
    from terracotta.handlers import rgb

    stretch_range = [100, 0]
    ds_keys = ['val21', 'x', 'val22']

    with pytest.raises(exceptions.InvalidArgumentsError):
        rgb.rgb(ds_keys[:2], ['val22', 'val23', 'val24'], raster_file_xyz,
                stretch_ranges=[stretch_range] * 3)


def test_rgb_preview(use_testdb):
    import terracotta
    from terracotta.handlers import rgb
    raw_img = rgb.rgb(['val21', 'x'], ['val22', 'val23', 'val24'])
    img_data = np.asarray(Image.open(raw_img))
    assert img_data.shape == (*terracotta.get_settings().DEFAULT_TILE_SIZE, 3)
