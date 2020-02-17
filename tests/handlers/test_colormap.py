import numpy as np
from PIL import Image

import pytest


def test_colormap_handler():
    from terracotta.handlers import colormap
    cmap = colormap.colormap(colormap='jet', stretch_range=[0., 1.], num_values=50)
    assert cmap
    assert len(cmap) == 50
    assert len(cmap[0]['rgba']) == 4
    assert cmap[0]['value'] == 0. and cmap[-1]['value'] == 1.


@pytest.mark.parametrize('stretch_range', [[0, 20000], [20000, 30000], [-50000, 50000]])
@pytest.mark.parametrize('cmap_name', [None, 'jet'])
def test_colormap_consistency(use_testdb, testdb, raster_file_xyz,
                              stretch_range, cmap_name):
    """Test consistency between /colormap and images returned by /singleband"""
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import singleband, colormap

    ds_keys = ['val21', 'x', 'val22']

    # get image with applied stretch and colormap
    raw_img = singleband.singleband(ds_keys, raster_file_xyz, stretch_range=stretch_range,
                                    colormap=cmap_name)
    img_data = np.asarray(Image.open(raw_img).convert('RGBA'))

    # get raw data to compare to
    driver = terracotta.get_driver(testdb)

    with driver.connect():
        tile_data = get_tile_data(driver, ds_keys, tile_xyz=raster_file_xyz,
                                  tile_size=img_data.shape[:2])

    # make sure all pixel values are included in colormap
    num_values = stretch_range[1] - stretch_range[0] + 1

    # get colormap for given stretch
    cmap = colormap.colormap(colormap=cmap_name, stretch_range=stretch_range,
                             num_values=num_values)
    cmap = dict(row.values() for row in cmap)

    # test nodata
    nodata_mask = tile_data.mask
    assert np.all(img_data[nodata_mask, -1] == 0)

    # test clipping
    below_mask = tile_data < stretch_range[0]
    assert np.all(img_data[below_mask & ~nodata_mask, :-1] == cmap[stretch_range[0]][:-1])

    above_mask = tile_data > stretch_range[1]
    assert np.all(img_data[above_mask & ~nodata_mask, :-1] == cmap[stretch_range[1]][:-1])

    # test values inside stretch_range
    values_to_test = np.unique(tile_data.compressed())
    values_to_test = values_to_test[(values_to_test >= stretch_range[0])
                                    & (values_to_test <= stretch_range[1])]

    for val in values_to_test:
        rgba = cmap[val]
        assert np.all(img_data[tile_data == val] == rgba)
