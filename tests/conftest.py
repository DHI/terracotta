import os
import multiprocessing
import time
from functools import partial

import pytest

import numpy as np
import rasterio


def pytest_configure(config):
    os.environ['TC_TESTING'] = '1'


def pytest_unconfigure(config):
    os.environ['TC_TESTING'] = '0'


@pytest.fixture(autouse=True)
def restore_settings():
    import terracotta
    from terracotta.config import TerracottaSettings

    try:
        yield
    finally:
        terracotta._settings = TerracottaSettings()
        terracotta._overwritten_settings = set()


def pytest_addoption(parser):
    parser.addoption(
        '--mysql-server',
        help='MySQL server to use for testing in the form of user:password@host:port'
    )


@pytest.fixture()
def mysql_server(request):
    return request.config.getoption('mysql_server')


def pytest_generate_tests(metafunc):
    if 'mysql_server' in metafunc.fixturenames:
        value = metafunc.config.getoption('mysql_server')
        metafunc.parametrize('mysql_server', [value])


def cloud_optimize(raster_file, outfile):
    import math
    import contextlib
    import rasterio
    import rasterio.io
    import rasterio.shutil

    COG_PROFILE = {
        'count': 1,
        'driver': 'GTiff',
        'interleave': 'pixel',
        'tiled': True,
        'blockxsize': 256,
        'blockysize': 256,
        'compress': 'DEFLATE',
        'photometric': 'MINISBLACK',
        'BIGTIFF': 'IF_SAFER'
    }

    with contextlib.ExitStack() as es:
        es.enter_context(rasterio.Env(
            GDAL_TIFF_INTERNAL_MASK=True,
            GDAL_TIFF_OVR_BLOCKSIZE=256,
        ))
        src = es.enter_context(rasterio.open(str(raster_file)))

        profile = src.profile.copy()
        profile.update(COG_PROFILE)

        memfile = es.enter_context(rasterio.io.MemoryFile())
        dst = es.enter_context(memfile.open(**profile))

        dst.write(src.read())

        max_overview_level = math.ceil(math.log2(max(
            dst.height // profile['blockysize'],
            dst.width // profile['blockxsize']
        )))

        overviews = [2 ** j for j in range(1, max_overview_level + 1)]
        rs_method = rasterio.enums.Resampling.nearest
        dst.build_overviews(overviews, rs_method)
        rasterio.shutil.copy(dst, str(outfile), copy_src_overviews=True, **COG_PROFILE)


@pytest.fixture(scope='session')
def raster_file(tmpdir_factory):
    import affine

    raster_data = np.arange(-128 * 256, 128 * 256, dtype='int16').reshape(256, 256)

    profile = {
        'driver': 'GTiff',
        'dtype': 'int16',
        'nodata': 10000,
        'width': raster_data.shape[1],
        'height': raster_data.shape[0],
        'count': 1,
        'crs': {'init': 'epsg:32637'},
        'transform': affine.Affine(
            2.0, 0.0, 694920.0,
            0.0, -2.0, 2055666.0
        )
    }

    outpath = tmpdir_factory.mktemp('raster')
    unoptimized_raster = outpath.join('img-raw.tif')
    with rasterio.open(str(unoptimized_raster), 'w', **profile) as dst:
        dst.write(raster_data, 1)

    optimized_raster = outpath.join('img.tif')
    cloud_optimize(unoptimized_raster, optimized_raster)

    return optimized_raster


@pytest.fixture(scope='session')
def raster_file_3857(tmpdir_factory, raster_file):
    import rasterio.warp
    from terracotta.drivers.raster_base import RasterDriver

    target_crs = RasterDriver.TARGET_CRS
    outpath = tmpdir_factory.mktemp('raster')
    unoptimized_raster = outpath.join('img-raw.tif')

    with rasterio.open(str(raster_file)) as src:
        out_transform, out_width, out_height = RasterDriver._calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds
        )
        out_profile = src.profile.copy()
        out_profile.update(
            width=out_width,
            height=out_height,
            crs=target_crs,
            transform=out_transform
        )

        with rasterio.open(str(unoptimized_raster), 'w', **out_profile) as dst:
            rasterio.warp.reproject(rasterio.band(src, 1), rasterio.band(dst, 1))

    optimized_raster = outpath.join('img.tif')
    cloud_optimize(unoptimized_raster, optimized_raster)

    return optimized_raster


@pytest.fixture(scope='session')
def big_raster_file(tmpdir_factory):
    import affine

    np.random.seed(17)
    raster_data = np.random.randint(0, np.iinfo(np.uint16).max, size=(1024, 1024), dtype='uint16')

    # include some big nodata regions
    ix, iy = np.indices(raster_data.shape)
    circular_mask = np.sqrt((ix - raster_data.shape[0] / 2) ** 2
                            + (iy - raster_data.shape[1] / 2) ** 2) > 400
    raster_data[circular_mask] = 0
    raster_data[200:600, 400:800] = 0
    raster_data[500, :] = 0

    profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': 0,
        'width': raster_data.shape[1],
        'height': raster_data.shape[0],
        'count': 1,
        'crs': {'init': 'epsg:32637'},
        'transform': affine.Affine(
            2.0, 0.0, 694920.0,
            0.0, -2.0, 2055666.0
        )
    }

    outpath = tmpdir_factory.mktemp('raster')
    unoptimized_raster = outpath.join('img-raw.tif')
    with rasterio.open(str(unoptimized_raster), 'w', **profile) as dst:
        dst.write(raster_data, 1)

    optimized_raster = outpath.join('img.tif')
    cloud_optimize(unoptimized_raster, optimized_raster)

    return optimized_raster


@pytest.fixture(scope='session')
def unoptimized_raster_file(tmpdir_factory):
    import affine

    np.random.seed(17)
    raster_data = np.random.randint(0, np.iinfo(np.uint16).max, size=(1024, 1024), dtype='uint16')

    # include some big nodata regions
    ix, iy = np.indices(raster_data.shape)
    circular_mask = np.sqrt((ix - raster_data.shape[0] / 2) ** 2
                            + (iy - raster_data.shape[1] / 2) ** 2) > 400
    raster_data[circular_mask] = 0
    raster_data[200:600, 400:800] = 0
    raster_data[500, :] = 0

    profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': 0,
        'width': raster_data.shape[1],
        'height': raster_data.shape[0],
        'count': 1,
        'crs': {'init': 'epsg:32637'},
        'transform': affine.Affine(
            2.0, 0.0, 694920.0,
            0.0, -2.0, 2055666.0
        )
    }

    outpath = tmpdir_factory.mktemp('raster')
    unoptimized_raster = outpath.join('img-raw.tif')
    with rasterio.open(str(unoptimized_raster), 'w', **profile) as dst:
        dst.write(raster_data, 1)

    return unoptimized_raster


@pytest.fixture(scope='session')
def invalid_raster_file(tmpdir_factory):
    """A raster file that is all nodata"""
    import affine

    raster_data = np.full((256, 256), 0, dtype='uint16')
    profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': 0,
        'width': raster_data.shape[1],
        'height': raster_data.shape[0],
        'count': 1,
        'crs': {'init': 'epsg:32637'},
        'transform': affine.Affine(
            2.0, 0.0, 694920.0,
            0.0, -2.0, 2055666.0
        )
    }

    outpath = tmpdir_factory.mktemp('raster')
    unoptimized_raster = outpath.join('img-raw.tif')
    with rasterio.open(str(unoptimized_raster), 'w', **profile) as dst:
        dst.write(raster_data, 1)

    optimized_raster = outpath.join('img.tif')
    cloud_optimize(unoptimized_raster, optimized_raster)

    return optimized_raster


@pytest.fixture(scope='session')
def raster_file_xyz(raster_file):
    import rasterio
    import rasterio.warp
    import mercantile

    with rasterio.open(str(raster_file)) as src:
        raster_bounds = rasterio.warp.transform_bounds(src.crs, 'epsg:4326', *src.bounds)
    raster_center_x = (raster_bounds[0] + raster_bounds[2]) / 2
    raster_center_y = (raster_bounds[1] + raster_bounds[3]) / 2

    zoom = 12
    tile = mercantile.tile(raster_center_x, raster_center_y, zoom)
    return (tile.x, tile.y, zoom)


@pytest.fixture(scope='session')
def raster_file_xyz_lowzoom(raster_file):
    import rasterio
    import rasterio.warp
    import mercantile

    with rasterio.open(str(raster_file)) as src:
        raster_bounds = rasterio.warp.transform_bounds(src.crs, 'epsg:4326', *src.bounds)
    raster_center_x = (raster_bounds[0] + raster_bounds[2]) / 2
    raster_center_y = (raster_bounds[1] + raster_bounds[3]) / 2

    zoom = 10
    tile = mercantile.tile(raster_center_x, raster_center_y, zoom)
    return (tile.x, tile.y, zoom)


@pytest.fixture(scope='session')
def read_only_database(raster_file, raster_file_3857, tmpdir_factory):
    from terracotta import get_driver

    keys = ['key1', 'akey', 'key2']
    key_descriptions = {
        'key2': 'key2'
    }

    dbpath = tmpdir_factory.mktemp('db').join('db-readonly.sqlite')
    driver = get_driver(dbpath, provider='sqlite')
    driver.create(keys, key_descriptions=key_descriptions)

    metadata = driver.compute_metadata(str(raster_file), extra_metadata=['extra_data'])

    with driver.connect():
        driver.insert(('val11', 'x', 'val12'), str(raster_file), metadata=metadata)
        driver.insert(('val21', 'x', 'val22'), str(raster_file))
        driver.insert(('val21', 'x', 'val23'), str(raster_file))
        driver.insert(('val21', 'x', 'val24'), str(raster_file))

    return dbpath


@pytest.fixture()
def use_read_only_database(read_only_database, monkeypatch):
    import terracotta
    terracotta.update_settings(DRIVER_PATH=str(read_only_database))


def run_test_server(driver_path, port):
    from terracotta import update_settings
    update_settings(DRIVER_PATH=driver_path)

    from terracotta.server.flask_api import create_app
    create_app().run(port=port)


@pytest.fixture(scope='session')
def test_server(read_only_database):
    """Spawn a Terracotta server in a separate process"""
    port = 5555
    server_proc = multiprocessing.Process(
        target=partial(run_test_server, driver_path=str(read_only_database), port=port)
    )
    server_proc.start()
    try:
        # make sure server has started up
        time.sleep(1)
        assert server_proc.is_alive()
        yield f'localhost:{port}'
    finally:
        server_proc.terminate()
        server_proc.join(5)
        assert not server_proc.is_alive()
