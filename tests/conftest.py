# shapely has to be imported before rasterio to work around
# https://github.com/Toblerity/Shapely/issues/553
import shapely.geometry  # noqa: F401

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
    """Wipe settings after every test"""
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


def cloud_optimize(raster_file, outfile, create_mask=False, remove_nodata=False):
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

        if remove_nodata:
            profile['nodata'] = None

        memfile = es.enter_context(rasterio.io.MemoryFile())
        dst = es.enter_context(memfile.open(**profile))

        dst.write(src.read())

        if create_mask:
            dst.write_mask(src.dataset_mask().astype('uint8'))

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

    # Sprinkle in some more nodata
    raster_data.flat[::5] = 10000

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
def raster_file_float(raster_file, tmpdir_factory):
    with rasterio.open(str(raster_file)) as src:
        raster_data = src.read().astype('float32')

        # Add some NaNs
        raster_data[:, :100, :100] = np.nan

        profile = src.profile.copy()
        profile.update(dtype='float32')

    outpath = tmpdir_factory.mktemp('raster-float')
    unoptimized_raster = outpath.join('img-raw.tif')
    with rasterio.open(str(unoptimized_raster), 'w', **profile) as dst:
        dst.write(raster_data,)

    optimized_raster = outpath.join('img.tif')
    cloud_optimize(unoptimized_raster, optimized_raster)

    return optimized_raster


@pytest.fixture(scope='session')
def big_raster_file_nodata(tmpdir_factory):
    import affine

    np.random.seed(17)
    raster_data = np.random.randint(0, np.iinfo(np.uint16).max, size=(2048, 2048), dtype='uint16')
    nodata = 10000

    # include some big nodata regions
    ix, iy = np.indices(raster_data.shape)
    circular_mask = np.sqrt((ix - raster_data.shape[0] / 2) ** 2
                            + (iy - raster_data.shape[1] / 2) ** 2) > 1000
    raster_data[circular_mask] = nodata
    raster_data[500:1000, 1000:2000] = nodata
    raster_data[1200, :] = nodata

    profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': nodata,
        'width': raster_data.shape[1],
        'height': raster_data.shape[0],
        'count': 1,
        'crs': {'init': 'epsg:32637'},
        'transform': affine.Affine(
            10.0, 0.0, 694920.0,
            0.0, -10.0, 2055666.0
        )
    }

    outpath = tmpdir_factory.mktemp('raster')
    unoptimized_raster = outpath.join('img-raw.tif')
    with rasterio.open(str(unoptimized_raster), 'w', **profile) as dst:
        dst.write(raster_data, 1)

    optimized_raster = outpath.join('img-nodata.tif')
    cloud_optimize(unoptimized_raster, optimized_raster)

    return optimized_raster


@pytest.fixture(scope='session')
def big_raster_file_mask(tmpdir_factory, big_raster_file_nodata):
    outpath = tmpdir_factory.mktemp('raster')
    optimized_raster = outpath.join('img-alpha.tif')
    cloud_optimize(big_raster_file_nodata, optimized_raster,
                   create_mask=True, remove_nodata=False)
    return optimized_raster


@pytest.fixture(scope='session')
def big_raster_file_nomask(tmpdir_factory, big_raster_file_nodata):
    outpath = tmpdir_factory.mktemp('raster')
    optimized_raster = outpath.join('img-alpha.tif')
    cloud_optimize(big_raster_file_nodata, optimized_raster,
                   create_mask=False, remove_nodata=True)
    return optimized_raster


@pytest.fixture(scope='session')
def unoptimized_raster_file(tmpdir_factory):
    import affine

    np.random.seed(17)
    raster_data = np.random.randint(0, np.iinfo(np.uint16).max, size=(1024, 1024), dtype='uint16')
    nodata = 10000

    # include some big nodata regions
    ix, iy = np.indices(raster_data.shape)
    circular_mask = np.sqrt((ix - raster_data.shape[0] / 2) ** 2
                            + (iy - raster_data.shape[1] / 2) ** 2) > 400
    raster_data[circular_mask] = nodata
    raster_data[200:600, 400:800] = nodata
    raster_data[500, :] = nodata

    profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': nodata,
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

    zoom = 14
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
def testdb(raster_file, tmpdir_factory):
    """A read-only, pre-populated test database"""
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
def use_testdb(testdb, monkeypatch):
    import terracotta
    terracotta.update_settings(DRIVER_PATH=str(testdb))


def run_test_server(driver_path, port):
    from terracotta import update_settings
    update_settings(DRIVER_PATH=driver_path)

    from terracotta.server.flask_api import create_app
    create_app().run(port=port)


@pytest.fixture(scope='session')
def test_server(testdb):
    """Spawn a Terracotta server in a separate process"""
    port = 5555
    server_proc = multiprocessing.Process(
        target=partial(run_test_server, driver_path=str(testdb), port=port)
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


@pytest.fixture()
def driver_path(provider, tmpdir, mysql_server):
    """Get a valid, uninitialized driver path for given provider"""
    import random
    import string

    from urllib.parse import urlparse

    def validate_con_info(con_info):
        return (con_info.scheme == 'mysql'
                and con_info.hostname
                and con_info.username
                and not con_info.path)

    def random_string(length):
        return ''.join(random.choices(string.ascii_uppercase, k=length))

    if provider == 'sqlite':
        dbfile = tmpdir.join('test.sqlite')
        yield str(dbfile)

    elif provider == 'mysql':
        if not mysql_server:
            return pytest.skip('mysql_server argument not given')

        if not mysql_server.startswith('mysql://'):
            mysql_server = f'mysql://{mysql_server}'

        con_info = urlparse(mysql_server)
        if not validate_con_info(con_info):
            raise ValueError('invalid value for mysql_server')

        dbpath = random_string(24)

        import pymysql
        try:
            with pymysql.connect(host=con_info.hostname, user=con_info.username,
                                 password=con_info.password):
                pass
        except pymysql.OperationalError as exc:
            raise RuntimeError('error connecting to MySQL server') from exc

        try:
            yield f'{mysql_server}/{dbpath}'

        finally:  # cleanup
            with pymysql.connect(host=con_info.hostname, user=con_info.username,
                                 password=con_info.password) as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.execute(f'DROP DATABASE IF EXISTS {dbpath}')
                    except pymysql.Warning:
                        pass

    else:
        return NotImplementedError(f'unknown provider {provider}')
