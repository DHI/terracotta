"""Benchmarks for all performance-critical use cases

Run separately via `pytest tests/benchmarks.py`.
"""

import pytest
from click.testing import CliRunner

ZOOM_XYZ = {
    'birds-eye': 8,
    'balanced': 12,
    'subpixel': 21,
    'preview': None
}


@pytest.fixture(scope='session')
def benchmark_database(big_raster_file_nodata, big_raster_file_mask, tmpdir_factory):
    from terracotta import get_driver, update_settings

    keys = ['type', 'band']

    update_settings(RASTER_CACHE_SIZE=0)

    dbpath = tmpdir_factory.mktemp('db').join('db-readonly.sqlite')
    driver = get_driver(dbpath, provider='sqlite')
    driver.create(keys)

    mtd = driver.compute_metadata(str(big_raster_file_nodata))

    with driver.connect():
        driver.insert(['nodata', '1'], str(big_raster_file_nodata), metadata=mtd)
        driver.insert(['nodata', '2'], str(big_raster_file_nodata), metadata=mtd)
        driver.insert(['nodata', '3'], str(big_raster_file_nodata), metadata=mtd)
        driver.insert(['mask', '1'], str(big_raster_file_mask), metadata=mtd)

    return dbpath


def get_xyz(raster_file, zoom):
    import rasterio
    import rasterio.warp
    import mercantile

    with rasterio.open(str(raster_file)) as src:
        raster_bounds = rasterio.warp.transform_bounds(src.crs, 'epsg:4326', *src.bounds)
    raster_center_x = (raster_bounds[0] + raster_bounds[2]) / 2
    raster_center_y = (raster_bounds[1] + raster_bounds[3]) / 2

    tile = mercantile.tile(raster_center_x, raster_center_y, zoom)
    return (tile.x, tile.y, zoom)


@pytest.mark.parametrize('resampling', ['nearest', 'linear', 'cubic', 'average'])
@pytest.mark.parametrize('zoom', ZOOM_XYZ.keys())
def test_bench_rgb(benchmark, zoom, resampling, big_raster_file_nodata, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings

    update_settings(
        DRIVER_PATH=str(benchmark_database),
        RESAMPLING_METHOD=resampling,
        REPROJECTION_METHOD=resampling
    )

    zoom_level = ZOOM_XYZ[zoom]

    flask_app = create_app()
    with flask_app.test_client() as client:
        if zoom_level is not None:
            x, y, z = get_xyz(big_raster_file_nodata, zoom_level)
            rv = benchmark(client.get, f'/rgb/nodata/{z}/{x}/{y}.png?r=1&g=2&b=3')
        else:
            rv = benchmark(client.get, '/rgb/nodata/preview.png?r=1&g=2&b=3')

    assert rv.status_code == 200


def test_bench_rgb_out_of_bounds(benchmark, big_raster_file_nodata, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings

    update_settings(DRIVER_PATH=str(benchmark_database))

    x, y, z = 0, 0, 20

    flask_app = create_app()
    with flask_app.test_client() as client:
        rv = benchmark(client.get, f'/rgb/nodata/{z}/{x}/{y}.png?r=1&g=2&b=3')

    assert rv.status_code == 200


@pytest.mark.parametrize('resampling', ['nearest', 'linear', 'cubic', 'average'])
@pytest.mark.parametrize('zoom', ZOOM_XYZ.keys())
def test_bench_singleband(benchmark, zoom, resampling, big_raster_file_nodata, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings, get_driver

    update_settings(
        DRIVER_PATH=str(benchmark_database),
        RESAMPLING_METHOD=resampling,
        REPROJECTION_METHOD=resampling
    )

    zoom_level = ZOOM_XYZ[zoom]

    flask_app = create_app()
    with flask_app.test_client() as client:
        if zoom_level is not None:
            x, y, z = get_xyz(big_raster_file_nodata, zoom_level)
            rv = benchmark(client.get, f'/singleband/nodata/1/{z}/{x}/{y}.png')
        else:
            rv = benchmark(client.get, '/singleband/nodata/1/preview.png')

    assert rv.status_code == 200
    assert not len(get_driver(str(benchmark_database))._raster_cache)


def test_bench_singleband_out_of_bounds(benchmark, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings

    update_settings(DRIVER_PATH=str(benchmark_database))

    x, y, z = 0, 0, 20

    flask_app = create_app()
    with flask_app.test_client() as client:
        rv = benchmark(client.get, f'/singleband/nodata/1/{z}/{x}/{y}.png')

    assert rv.status_code == 200


@pytest.mark.parametrize('chunks', [False, True])
@pytest.mark.parametrize('raster_type', ['nodata', 'masked'])
def test_bench_compute_metadata(benchmark, big_raster_file_nodata, big_raster_file_mask,
                                chunks, raster_type):
    from terracotta.drivers.raster_base import RasterDriver
    if raster_type == 'nodata':
        raster_file = big_raster_file_nodata
    elif raster_type == 'masked':
        raster_file = big_raster_file_mask
    benchmark(RasterDriver.compute_metadata, str(raster_file), use_chunks=chunks)


@pytest.mark.parametrize('in_memory', [False, True])
def test_bench_optimize_rasters(benchmark, unoptimized_raster_file, tmpdir, in_memory):
    from terracotta.scripts import cli

    input_pattern = str(unoptimized_raster_file.dirpath('*.tif'))
    in_memory_flag = '--in-memory' if in_memory else '--no-in-memory'

    runner = CliRunner()
    result = benchmark(
        runner.invoke, cli.cli,
        ['optimize-rasters', input_pattern, '-o', str(tmpdir), in_memory_flag, '--overwrite']
    )

    assert result.exit_code == 0
