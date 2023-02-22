from PIL import Image
import numpy as np

import pytest


@pytest.mark.parametrize('resampling_method', ['nearest', 'linear', 'cubic', 'average'])
def test_singleband_handler(use_testdb, raster_file_xyz,
                            resampling_method):
    import terracotta
    terracotta.update_settings(RESAMPLING_METHOD=resampling_method)

    from terracotta.handlers import datasets, singleband
    settings = terracotta.get_settings()
    ds = datasets.datasets()

    for keys in ds:
        raw_img = singleband.singleband(keys, raster_file_xyz)
        img_data = np.asarray(Image.open(raw_img))
        assert img_data.shape == settings.DEFAULT_TILE_SIZE


def test_singleband_tile_size(use_testdb, raster_file_xyz):
    from terracotta.handlers import datasets, singleband
    ds = datasets.datasets()

    test_tile_size = (16, 32)

    for keys in ds:
        raw_img = singleband.singleband(keys, raster_file_xyz, tile_size=test_tile_size)
        img_data = np.asarray(Image.open(raw_img))
        assert img_data.shape == test_tile_size


def test_singleband_out_of_bounds(use_testdb):
    import terracotta
    from terracotta.handlers import datasets, singleband
    ds = datasets.datasets()

    for keys in ds:
        with pytest.raises(terracotta.exceptions.TileOutOfBoundsError):
            singleband.singleband(keys, (10, 0, 0))


def test_singleband_explicit_colormap(use_testdb, testdb, raster_file_xyz):
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import singleband

    ds_keys = ['val21', 'x', 'val22']
    nodata = 10000

    settings = terracotta.get_settings()
    driver = terracotta.get_driver(testdb)
    with driver.connect():
        tile_data = get_tile_data(driver, ds_keys, tile_xyz=raster_file_xyz,
                                  preserve_values=True, tile_size=settings.DEFAULT_TILE_SIZE)

    # Get some values from the raster to use for colormap
    classes = np.unique(tile_data)
    classes = classes[:254]

    colormap = {}
    for i in range(classes.shape[0]):
        val = classes[i]
        color = val % 256
        colormap[val] = (color, color, color, color)
    colormap[nodata] = (100, 100, 100, 100)

    raw_img = singleband.singleband(ds_keys, raster_file_xyz, colormap=colormap)
    img_data = np.asarray(Image.open(raw_img).convert('RGBA'))

    # get unstretched data to compare to
    with driver.connect():
        tile_data = get_tile_data(driver, ds_keys, tile_xyz=raster_file_xyz,
                                  preserve_values=True, tile_size=img_data.shape[:2])

    # check that labels are mapped to colors correctly
    for cmap_label, cmap_color in colormap.items():
        if cmap_label == nodata:
            # make sure nodata is still transparent
            assert np.all(img_data[tile_data == cmap_label, -1] == 0)
        else:
            assert np.all(img_data[tile_data == cmap_label] == np.asarray(cmap_color))

    # check that all data outside of labels is transparent
    keys_arr = np.array(list(colormap.keys()), dtype=np.int16)
    assert np.all(img_data[~np.isin(tile_data, keys_arr), -1] == 0)


def test_singleband_noxyz(use_testdb):
    from terracotta import get_settings
    from terracotta.handlers import singleband

    settings = get_settings()
    ds_keys = ['val21', 'x', 'val22']

    raw_img = singleband.singleband(ds_keys)
    img_data = np.asarray(Image.open(raw_img))

    assert img_data.shape == settings.DEFAULT_TILE_SIZE
