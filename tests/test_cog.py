import pytest

import affine
import rasterio
from rasterio.io import MemoryFile
from rasterio.shutil import copy
from rasterio.enums import Resampling

import numpy as np

BASE_PROFILE = {
    'driver': 'GTiff',
    'dtype': 'uint16',
    'nodata': 0,
    'count': 1,
    'crs': {'init': 'epsg:32637'},
    'transform': affine.Affine(
        2.0, 0.0, 694920.0,
        0.0, -2.0, 2055666.0
    )
}


def test_validate_optimized(tmpdir):
    from terracotta import cog

    outfile = str(tmpdir / 'raster.tif')
    raster_data = 1000 * np.random.rand(512, 512).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1],
        tiled=True,
        blockxsize=256,
        blockysize=256
    )

    with MemoryFile() as mf, mf.open(**profile) as dst:
        dst.write(raster_data, 1)

        overviews = [2 ** j for j in range(1, 4)]
        dst.build_overviews(overviews, Resampling.nearest)

        copy(dst, outfile, copy_src_overviews=True, **profile)

    assert cog.validate(outfile)


def test_validate_optimized_small(tmpdir):
    from terracotta import cog

    outfile = str(tmpdir / 'raster.tif')
    raster_data = 1000 * np.random.rand(128, 128).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1]
    )

    with rasterio.open(outfile, 'w', **profile) as dst:
        dst.write(raster_data, 1)

    assert cog.validate(outfile)


def test_validate_unoptimized(tmpdir):
    from terracotta import cog

    outfile = str(tmpdir / 'raster.tif')
    raster_data = 1000 * np.random.rand(512, 512).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1]
    )

    with rasterio.open(outfile, 'w', **profile) as dst:
        dst.write(raster_data, 1)

    assert not cog.validate(outfile)


def test_validate_no_overviews(tmpdir):
    from terracotta import cog

    outfile = str(tmpdir / 'raster.tif')
    raster_data = 1000 * np.random.rand(512, 512).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1],
        tiled=True,
        blockxsize=256,
        blockysize=256
    )

    with rasterio.open(outfile, 'w', **profile) as dst:
        dst.write(raster_data, 1)

    assert not cog.validate(outfile)


def test_validate_not_tiled(tmpdir):
    from terracotta import cog

    outfile = str(tmpdir / 'raster.tif')
    raster_data = 1000 * np.random.rand(512, 512).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1]
    )

    with rasterio.open(outfile, 'w', **profile) as dst:
        dst.write(raster_data, 1)

        overviews = [2 ** j for j in range(1, 4)]
        dst.build_overviews(overviews, Resampling.nearest)

    assert not cog.validate(outfile)


def test_validate_wrong_offset(tmpdir):
    from terracotta import cog

    outfile = str(tmpdir / 'raster.tif')
    raster_data = 1000 * np.random.rand(512, 512).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1],
        tiled=True,
        blockxsize=256,
        blockysize=256
    )

    with rasterio.open(outfile, 'w', **profile) as dst:
        dst.write(raster_data, 1)

        overviews = [2 ** j for j in range(1, 4)]
        dst.build_overviews(overviews, Resampling.nearest)

    assert not cog.validate(outfile)


def test_validate_external_overview(tmpdir):
    import os
    from terracotta import cog

    outfile = str(tmpdir / 'raster.tif')
    raster_data = 1000 * np.random.rand(512, 512).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1],
        tiled=True,
        blockxsize=256,
        blockysize=256
    )

    with rasterio.Env(TIFF_USE_OVR=True):
        with rasterio.open(outfile, 'w', **profile) as dst:
            dst.write(raster_data, 1)

            overviews = [2 ** j for j in range(1, 4)]
            dst.build_overviews(overviews, Resampling.nearest)

        assert os.path.isfile(f'{outfile}.ovr')

    assert not cog.validate(outfile)


@pytest.mark.filterwarnings("ignore:Dataset has no geotransform set")
def test_validate_not_gtiff(tmpdir):
    from terracotta import cog

    outfile = str(tmpdir / 'raster.png')
    raster_data = 1000 * np.random.rand(512, 512).astype(np.uint16)

    profile = BASE_PROFILE.copy()
    profile.update(
        height=raster_data.shape[0],
        width=raster_data.shape[1],
        driver='PNG'
    )

    with rasterio.open(outfile, 'w', **profile) as dst:
        dst.write(raster_data, 1)

    assert not cog.validate(outfile)
