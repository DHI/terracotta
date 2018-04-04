import os

import numpy as np
import mercantile
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling


class TileNotFoundError(Exception):
    pass


class TileOutOfBoundsError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


def _requires_dataset(func):
    """Decorator for TileStore that checks if dataset exists in the TileStore
    and throws a DatasetNotFoundError if it doesnt."""
    def inner(self, dataset, *args, **kwargs):
        if dataset not in self._datasets:
            raise DatasetNotFoundError('dataset {} not found'.format(dataset))
        return func(self, dataset, *args, **kwargs)
    return inner


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

    def get_datasets(self):
        return self._datasets.keys()

    @_requires_dataset
    def get_meta(self, dataset):
        return self._datasets[dataset]['meta']

    @_requires_dataset
    def get_timesteps(self, dataset):
        if not self._datasets[dataset]['timestepped']:
            return []
        return sorted(self._datasets[dataset]['timesteps'].keys())

    @_requires_dataset
    def get_nodata(self, dataset):
        return self._datasets[dataset]['meta']['nodata']

    @_requires_dataset
    def get_bounds(self, dataset):
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
                file_info['timesteps'][timestep] = os.path.join(path, m.group(0))
        else:
            # Only support 1 file per timestep for now
            assert len(matches) == 1
            file_info['filename'] = os.path.join(path, matches[0].group(0))

        meta = TileStore._load_file_meta([os.path.join(path, m.group(0)) for m in matches])
        file_info['meta'] = meta
        file_info['meta']['timestepped'] = timestepped

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
        data_min = float('inf')
        data_max = float('-inf')
        for f in files:
            with rasterio.open(f) as src:
                data = src.read(1)
                meta['wgs_bounds'] = transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds),
                                                      densify_pts=21)
                meta['nodata'] = src.nodata
                data_min = min(data_min, np.nanmin(data))
                data_max = max(data_max, np.nanmax(data))
            if first:
                first_meta = set(meta)
                first = False
            diff = set(meta) ^ first_meta
            if diff:
                raise ValueError('{} does not match other files in: {}'.format(f, diff))
        meta['range'] = (np.asscalar(data_min), np.asscalar(data_max))

        return meta

    def tile(self, tile_x, tile_y, tile_z, ds_name,
             timestep=None, tilesize=256):
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

        mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
        tile_bounds = mercantile.xy_bounds(mercator_tile)
        tile = self._load_tile(fname, tile_bounds, tilesize)

        alpha_mask = self._alpha_mask(tile, ds_name, tilesize)

        return tile, alpha_mask

    def _alpha_mask(self, tile, ds_name, tilesize):
        """Return alpha layer for tile, where nodata NaNs and Infs are transparent.
        
        Parameters
        ----------
        tile: np.array
            The image tile.
        ds_name: string
            Internal name of the dataset.
        tilesize: int
            length of one side of tile
        
        Returns
        -------
        out: np.array of uint8
            Array of alpha values"""

        alpha_mask = np.full((tilesize, tilesize), 255, np.uint8)
        nodata = self.get_nodata(ds_name)
        alpha_mask[tile == nodata] = 0

        # Also mask out other invalid values if float
        if np.issubdtype(tile.dtype, np.floating):
            alpha_mask[~np.isfinite(tile)] = 0

        return alpha_mask

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
