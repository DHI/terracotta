"""Benchmarks for all performance-critical use cases

Run separately via `pytest tests/benchmarks.py`.
"""

import pytest
from click.testing import CliRunner

import shutil

ZOOM_XYZ = {
    'birds-eye': 6,
    'subpixel': 22,
    'preview': None
}


@pytest.fixture(scope='session')
def cached_benchmark_database(big_raster_file, tmpdir_factory):
    from terracotta import get_driver

    keys = ['band']

    dbpath = tmpdir_factory.mktemp('db').join('db-readonly.sqlite')
    driver = get_driver(dbpath, provider='sqlite')
    driver.create(keys)

    mtd = driver.compute_metadata(str(big_raster_file))

    with driver.connect():
        driver.insert(['1'], str(big_raster_file), metadata=mtd)
        driver.insert(['2'], str(big_raster_file), metadata=mtd)
        driver.insert(['3'], str(big_raster_file), metadata=mtd)

    return dbpath


@pytest.fixture
def benchmark_database(cached_benchmark_database, tmpdir):
    """Always yields a fresh copy of the database to prevent caching"""
    dbpath = tmpdir.join('db-readonly.sqlite')
    shutil.copy(cached_benchmark_database, dbpath)
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
def test_bench_rgb(benchmark, zoom, resampling, big_raster_file, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings

    update_settings(
        DRIVER_PATH=str(benchmark_database),
        UPSAMPLING_METHOD=resampling,
        DOWNSAMPLING_METHOD=resampling,
        RASTER_CACHE_SIZE=0,
        METADATA_CACHE_SIZE=0
    )

    zoom_level = ZOOM_XYZ[zoom]

    flask_app = create_app()
    with flask_app.test_client() as client:
        if zoom_level is not None:
            x, y, z = get_xyz(big_raster_file, zoom_level)
            rv = benchmark(client.get, f'/rgb/{z}/{x}/{y}.png?r=1&g=2&b=3')
        else:
            rv = benchmark(client.get, f'/rgb/preview.png?r=1&g=2&b=3')

    assert rv.status_code == 200


def test_bench_rgb_out_of_bounds(benchmark, big_raster_file, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings

    update_settings(
        DRIVER_PATH=str(benchmark_database),
        RASTER_CACHE_SIZE=0,
        METADATA_CACHE_SIZE=0
    )

    x, y, z = 0, 0, 20

    flask_app = create_app()
    with flask_app.test_client() as client:
        rv = benchmark(client.get, f'/rgb/{z}/{x}/{y}.png?r=1&g=2&b=3')

    assert rv.status_code == 200


@pytest.mark.parametrize('resampling', ['nearest', 'linear', 'cubic', 'average'])
@pytest.mark.parametrize('zoom', ZOOM_XYZ.keys())
def test_bench_singleband(benchmark, zoom, resampling, big_raster_file, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings

    update_settings(
        DRIVER_PATH=str(benchmark_database),
        UPSAMPLING_METHOD=resampling,
        DOWNSAMPLING_METHOD=resampling,
        RASTER_CACHE_SIZE=0,
        METADATA_CACHE_SIZE=0
    )

    zoom_level = ZOOM_XYZ[zoom]

    flask_app = create_app()
    with flask_app.test_client() as client:
        if zoom_level is not None:
            x, y, z = get_xyz(big_raster_file, zoom_level)
            rv = benchmark(client.get, f'/singleband/1/{z}/{x}/{y}.png')
        else:
            rv = benchmark(client.get, f'/singleband/1/preview.png')

    assert rv.status_code == 200


def test_bench_singleband_out_of_bounds(benchmark, benchmark_database):
    from terracotta.server import create_app
    from terracotta import update_settings

    update_settings(
        DRIVER_PATH=str(benchmark_database),
        RASTER_CACHE_SIZE=0,
        METADATA_CACHE_SIZE=0
    )

    x, y, z = 0, 0, 20

    flask_app = create_app()
    with flask_app.test_client() as client:
        rv = benchmark(client.get, f'/singleband/1/{z}/{x}/{y}.png')

    assert rv.status_code == 200


@pytest.mark.parametrize('chunks', [False, True])
def test_bench_compute_metadata(benchmark, big_raster_file, chunks):
    from terracotta.drivers.raster_base import RasterDriver
    benchmark(RasterDriver.compute_metadata, str(big_raster_file), use_chunks=chunks)


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
