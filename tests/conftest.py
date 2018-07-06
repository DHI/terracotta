import os

import pytest

import numpy as np
import rasterio


def pytest_configure(config):
    os.environ['TC_TESTING'] = '1'


def pytest_unconfigure(config):
    os.environ['TC_TESTING'] = '0'


@pytest.fixture(scope='session')
def raster_file(tmpdir_factory):
    import affine

    raster_data = np.random.rand(256, 256).astype('float32')
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': np.nan,
        'width': raster_data.shape[1],
        'height': raster_data.shape[0],
        'count': 1,
        'crs': {'init': 'epsg:32637'},
        'transform': affine.Affine(
            2.0, 0.0, 694920.0,
            0.0, -2.0, 2055666.0
        )
    }

    outpath = tmpdir_factory.mktemp('raster').join('img.tif')
    with rasterio.open(str(outpath), 'w', **profile) as dst:
        dst.write(raster_data, 1)

    return outpath


@pytest.fixture(scope='session')
def raster_file_xyz(raster_file):
    import rasterio
    import rasterio.vrt
    import mercantile

    with rasterio.open(str(raster_file)) as src:
        with rasterio.vrt.WarpedVRT(src, crs='epsg:4326') as vrt:
            raster_bounds = vrt.bounds

    tile = mercantile.tile(raster_bounds[0], raster_bounds[3], 10)
    return (tile.x, tile.y, 10)


@pytest.fixture(scope='session')
def read_only_database(raster_file, tmpdir_factory):
    from terracotta import get_driver

    keys = ('key1', 'key2')

    dbpath = tmpdir_factory.mktemp('db').join('db-readonly.sqlite')
    driver = get_driver(dbpath, provider='sqlite')
    with driver.connect():
        driver.create(keys)
        driver.insert(('val11', 'val12'), str(raster_file), ['extra_data'])
        driver.insert(('val21', 'val22'), str(raster_file))
        driver.insert(('val21', 'val23'), str(raster_file))
        driver.insert(('val21', 'val24'), str(raster_file))

    return dbpath


@pytest.fixture()
def use_read_only_database(read_only_database, monkeypatch):
    import terracotta
    settings = terracotta.config.parse_config({'DRIVER_PATH': str(read_only_database)})
    with monkeypatch.context() as m:
        m.setattr(terracotta, 'get_settings', lambda: settings)
        yield
