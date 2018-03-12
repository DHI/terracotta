import os

import numpy as np
import mercantile
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling


DEFAULT_CACHE_SIZE = 256000000  # 256MB


class TileNotFoundError(Exception):
    pass


class TileOutOfBoundsError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


class TileStore:
    """Stores information about datasets and caches access to tiles."""

    def __init__(self, cfg_datasets):
        self._datasets = self._make_datasets(cfg_datasets)

    @staticmethod
    def _make_datasets(cfg_datasets):
        """Build datasets from parsed config sections.

        Parameters
        ----------
        cfg_datasets: list of dict
            Each dict represents a dataset config section"""

        datasets = {}
        for ds_name in cfg_datasets.keys():
            cfg_ds = cfg_datasets[ds_name]
            ds = {}
            ds['timestepped'] = cfg_ds['timestepped']
            file_params = TileStore._parse_files(cfg_ds['path'],
                                                 cfg_ds['timestepped'],
                                                 cfg_ds['regex'])
            ds.update(file_params)
            datasets[cfg_ds['name']] = ds
        return datasets

    def get_meta(self, dataset):
        if dataset not in self._datasets:
            raise DatasetNotFoundError('dataset {} not found'.format(dataset))
        return self._datasets[dataset]['meta'].copy()

    def get_nodata(self, dataset):
        if dataset not in self._datasets:
            raise DatasetNotFoundError('dataset {} not found'.format(dataset))
        return self._datasets[dataset]['meta']['nodata']

    def get_bounds(self, dataset):
        if dataset not in self._datasets:
            raise DatasetNotFoundError('dataset {} not found'.format(dataset))
        return self._datasets[dataset]['meta']['wgs_bounds']

    @staticmethod
    def _parse_files(path, timestepped, regex):
        """Discover file(s) from `path` and build
        file information dict.

        Parameters
        ----------
        path: str
            Path to GeoTiff file(s)
        timestepped: Bool
            If True, find multiple files. Assumes `regex` has a named 'timestamp' group.
        regex: str
            Compiled regex to match file(s). Matches timesteps on 'timestamp' group.
        """

        file_info = {}
        files = os.listdir(path)
        matches = map(regex.match, files)
        matches = [x for x in matches if x is not None]
        if not matches:
            raise ValueError('no files matched {} in {}'.format(regex.pattern, path))
        if timestepped:
            file_info['timesteps'] = {}
            for m in matches:
                timestep = m.group('timestamp')
                # Only support 1 file per timestep for now
                assert timestep not in file_info['timesteps']
                file_info['timesteps'][timestep] = m.group(0)
        else:
            # Only support 1 file per timestep for now
            assert len(matches) == 1
            file_info['filename'] = matches[0].group(0)

        meta = TileStore._load_file_meta([m.group(0) for m in matches])
        file_info['meta'] = meta

        return file_info

    @staticmethod
    def _load_file_meta(files):
        """Pre-load and pre-compute needed file metadata.
        Also validate that meta doesn't differ between timesteps.

        Parameters
        ----------
        path: str
            Path to the file.

        Returns
        -------
        out: dict
            Metadata."""

        meta = {}
        first = True
        for f in files:
            with rasterio.open(f) as src:
                data = src.read(1)
                meta['wgs_bounds'] = transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds),
                                                      densify_pts=21)
                meta['nodata'] = src.nodata
                meta['range'] = (np.min(data), np.max(data))
            if first:
                first_meta = meta.copy()
                first = False
            if meta != first_meta:
                diff = set(meta) - set(first_meta)
                raise ValueError('{} does not match other files in: {}'.format(f, diff))

        return meta

    def tile(self, tile_x, tile_y, tile_z, ds_name,
             timestep=None, tilesize=256, scale_contrast=False):
        """Load a requested tile from source.

        Parameters
        ----------
        tile_x: int
            Mercator tile X index.
        tile_y: int
            Mercator tile Y index.
        tile_z: int
            Mercator tile ZOOM level.
        """

        try:
            dataset = self._datasets[ds_name]
        except KeyError:
            raise TileNotFoundError('no such dataset {}'.format(ds_name))

        if not dataset['timestepped'] and timestep:
            raise TileNotFoundError('dataset {} is not timestepped'.format(ds_name))

        if timestep:
            try:
                fname = dataset['timesteps'][timestep]
            except KeyError:
                raise TileNotFoundError('no such timestep in dataset {}'.format(ds_name))
        else:
            fname = dataset['filename']

        if not tile_exists(dataset['meta']['wgs_bounds'], tile_z, tile_x, tile_y):
            raise TileOutOfBoundsError('Tile {}/{}/{} is outside image bounds'
                                       .format(tile_z, tile_x, tile_y))

        nodata = self.get_nodata(ds_name)
        mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
        tile_bounds = mercantile.xy_bounds(mercator_tile)
        tile = self._load_tile(fname, tile_bounds, tilesize)
        alpha_mask = np.full((tilesize, tilesize), 255, np.uint8)
        alpha_mask[tile == nodata] = 0
        if scale_contrast:
            tile = contrast_stretch(tile, self._datasets[ds_name]['meta']['range'])

        return tile, alpha_mask

    @staticmethod
    def _load_tile(path, bounds, tilesize):
        """Load tile within `bounds` from `path`.

        Parameters
        ----------
        path: str
            Path to file.
        bounds: mercantile.Bbox
            Bounds of tile.
        tilesize: int
            Output image shape is (tilesize, tilesize).

        Returns
        -------
        out: numpy array
            array of pixels within bounds."""

        try:
            with rasterio.open(path) as src:
                with WarpedVRT(src,
                               dst_crs='epsg:3857',
                               resampling=Resampling.bilinear) as vrt:
                    window = vrt.window(*bounds)
                    arr = vrt.read(1,
                                   window=window,
                                   out_shape=(tilesize, tilesize),
                                   boundless=True)
        except OSError:
            raise TileNotFoundError('error while reading file {}'.format(path))

        return arr


def tile_exists(bounds, tile_z, tile_x, tile_y):
    """Check if a mercatile tile is inside a given bounds.

    Parameters
    ----------
    bounds : list
        WGS84 bounds (left, bottom, right, top).
    x : int
        Mercator tile Y index.
    y : int
        Mercator tile Y index.
    z : int
        Mercator tile ZOOM level.

    Returns
    -------
    out : boolean
        if True, the z-x-y mercator tile in inside the bounds.
    """

    mintile = mercantile.tile(bounds[0], bounds[3], tile_z)
    maxtile = mercantile.tile(bounds[2], bounds[1], tile_z)

    return (tile_x <= maxtile.x + 1) \
        and (tile_x >= mintile.x) \
        and (tile_y <= maxtile.y + 1) \
        and (tile_y >= mintile.y)


def contrast_stretch(tile, val_range):
    """Scale the image to between 0 and 255.

    Parameters
    ----------
    val_range: (int, int)
        min and max value of input tile

    Returns
    -------
    out: numpy array
        input tile scaled to 0 - 255.
    """

    _, max_val = val_range
    tile *= 255 // max_val
    tile = tile.astype(np.uint8)
    return tile
