from PIL import Image
import numpy as np

import pytest


@pytest.mark.parametrize('upsampling_method', ['nearest', 'linear', 'cubic', 'average'])
def test_singleband_handler(use_read_only_database, raster_file_xyz,
                            upsampling_method):
    import terracotta
    terracotta.update_settings(UPSAMPLING_METHOD=upsampling_method)

    from terracotta.handlers import datasets, singleband
    settings = terracotta.get_settings()
    ds = datasets.datasets()

    for keys in ds:
        raw_img = singleband.singleband(keys, raster_file_xyz)
        img_data = np.asarray(Image.open(raw_img))
        assert img_data.shape == settings.DEFAULT_TILE_SIZE


def test_singleband_out_of_bounds(use_read_only_database):
    import terracotta
    from terracotta.handlers import datasets, singleband
    ds = datasets.datasets()

    for keys in ds:
        with pytest.raises(terracotta.exceptions.TileOutOfBoundsError):
            singleband.singleband(keys, (10, 0, 0))


def test_singleband_explicit_colormap(use_read_only_database, read_only_database,
                                      raster_file_xyz):
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import singleband

    ds_keys = ['val21', 'x', 'val22']
    colormap = {i: (i, i, i) for i in range(150)}

    raw_img = singleband.singleband(ds_keys, raster_file_xyz, colormap=colormap)
    img_data = np.asarray(Image.open(raw_img).convert('RGBA'))

    # get unstretched data to compare to
    driver = terracotta.get_driver(read_only_database)

    with driver.connect():
        tile_data = get_tile_data(driver, ds_keys, tile_xyz=raster_file_xyz,
                                  tile_size=img_data.shape[:2])

    # check that labels are mapped to colors correctly
    for cmap_label, cmap_color in colormap.items():
        assert np.all(img_data[tile_data == cmap_label] == np.array([*cmap_color, 255]))

    # check that all data outside of labels is transparent
    assert np.all(img_data[~np.isin(tile_data, colormap.keys()), -1] == 0)


def test_singleband_noxyz(use_read_only_database):
    from terracotta import get_settings
    from terracotta.handlers import singleband

    settings = get_settings()
    ds_keys = ['val21', 'x', 'val22']

    raw_img = singleband.singleband(ds_keys)
    img_data = np.asarray(Image.open(raw_img))

    assert img_data.shape == settings.DEFAULT_TILE_SIZE
