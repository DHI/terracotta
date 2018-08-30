from PIL import Image
import numpy as np

import pytest


@pytest.mark.parametrize('upsampling_method', ['nearest', 'linear', 'cubic', 'average'])
def test_singleband_handler(use_read_only_database, raster_file, raster_file_xyz,
                            upsampling_method):
    import terracotta
    terracotta.update_settings(UPSAMPLING_METHOD=upsampling_method)

    from terracotta.handlers import datasets, singleband
    settings = terracotta.get_settings()
    ds = datasets.datasets()

    for keys in ds:
        raw_img = singleband.singleband(keys, raster_file_xyz)
        img_data = np.asarray(Image.open(raw_img))
        assert img_data.shape == settings.TILE_SIZE


def test_singleband_out_of_bounds(use_read_only_database, raster_file):
    import terracotta
    from terracotta.handlers import datasets, singleband
    ds = datasets.datasets()

    for keys in ds:
        with pytest.raises(terracotta.exceptions.TileOutOfBoundsError):
            singleband.singleband(keys, (10, 0, 0))


@pytest.mark.parametrize('stretch_range', [[0, 20000], [10000, 20000], [-50000, 50000]])
def test_singleband_stretch(stretch_range, use_read_only_database, read_only_database, raster_file_xyz):
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import singleband

    ds_keys = ['val21', 'val22']

    raw_img = singleband.singleband(ds_keys, raster_file_xyz, stretch_range=stretch_range)
    img_data = np.asarray(Image.open(raw_img))

    # get unstretched data to compare to
    driver = terracotta.get_driver(read_only_database)

    tile_x, tile_y, tile_z = raster_file_xyz

    with driver.connect():
        tile_data = get_tile_data(driver, ds_keys, tile_x=tile_x, tile_y=tile_y, tile_z=tile_z,
                                  tilesize=img_data.shape)
    
    # filter transparent values
    valid_mask = tile_data != 0
    assert np.all(img_data[~valid_mask] == 0)

    valid_img = img_data[valid_mask]
    valid_data = tile_data[valid_mask]

    assert np.all(valid_img[valid_data < stretch_range[0]] == 1)
    stretch_range_mask = (valid_data > stretch_range[0]) & (valid_data < stretch_range[1])
    assert not np.any(np.isin(valid_img[stretch_range_mask], [1, 255]))
    assert np.all(valid_img[valid_data > stretch_range[1]] == 255)
