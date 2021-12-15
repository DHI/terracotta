from PIL import Image
import numpy as np


def test_compute_handler(use_testdb, raster_file_xyz):
    import terracotta
    from terracotta.handlers import compute
    settings = terracotta.get_settings()

    raw_img = compute.compute(
        'v1 + v2',
        ['val21', 'x'],
        {'v1': 'val22', 'v2': 'val23'},
        stretch_range=(0, 10000),
        tile_xyz=raster_file_xyz
    )
    img_data = np.asarray(Image.open(raw_img))
    assert img_data.shape == settings.DEFAULT_TILE_SIZE


def test_compute_consistency(use_testdb, testdb, raster_file_xyz):
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import compute
    from terracotta.image import to_uint8

    settings = terracotta.get_settings()

    raw_img = compute.compute(
        'v1 + v2',
        ['val21', 'x'],
        {'v1': 'val22', 'v2': 'val23'},
        stretch_range=(0, 10000),
        tile_xyz=raster_file_xyz
    )
    img_data = np.asarray(Image.open(raw_img))
    assert img_data.shape == settings.DEFAULT_TILE_SIZE

    driver = terracotta.get_driver(testdb)

    with driver.connect():
        v1 = get_tile_data(driver, ['val21', 'x', 'val22'], raster_file_xyz)
        v2 = get_tile_data(driver, ['val21', 'x', 'val23'], raster_file_xyz)

    np.testing.assert_array_equal(
        img_data,
        to_uint8(v1 + v2, 0, 10000)
    )


def test_compute_transparency_nan(use_testdb, testdb, raster_file_xyz):
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import compute

    raw_img = compute.compute(
        'where(v1 > 0, nan, v1 + v2)',
        ['val21', 'x'],
        {'v1': 'val22', 'v2': 'val23'},
        stretch_range=(0, 10000),
        tile_xyz=raster_file_xyz
    )
    img_data = np.asarray(Image.open(raw_img).convert('RGBA'))

    driver = terracotta.get_driver(testdb)

    with driver.connect():
        v1 = get_tile_data(driver, ['val21', 'x', 'val22'], raster_file_xyz)

    alpha = img_data[..., 3]
    np.testing.assert_array_equal(
        alpha,
        np.where(v1.mask | (v1 > 0), 0, 255),
    )


def test_compute_transparency_mask(use_testdb, testdb, raster_file_xyz):
    import terracotta
    from terracotta.xyz import get_tile_data
    from terracotta.handlers import compute

    raw_img = compute.compute(
        'masked_where(v1 > 0, v1 + v2)',
        ['val21', 'x'],
        {'v1': 'val22', 'v2': 'val23'},
        stretch_range=(0, 10000),
        tile_xyz=raster_file_xyz
    )
    img_data = np.asarray(Image.open(raw_img).convert('RGBA'))

    driver = terracotta.get_driver(testdb)

    with driver.connect():
        v1 = get_tile_data(driver, ['val21', 'x', 'val22'], raster_file_xyz)

    alpha = img_data[..., 3]
    np.testing.assert_array_equal(
        alpha,
        np.where(v1.mask | (v1 > 0), 0, 255),
    )
