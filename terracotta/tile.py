import operator
import configparser

import numpy as np
import mercantile
import rasterio
from frozendict import frozendict
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
from cachetools import LFUCache, cachedmethod

import terracotta.config as config


class TileNotFoundError(Exception):
    pass


class TileOutOfBoundsError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


def _requires_dataset(func):
    """Decorator for TileStore that checks if dataset exists in the TileStore
    and throws a DatasetNotFoundError if it doesn't."""
    def inner(self, dataset, *args, **kwargs):
        if dataset not in self._datasets:
            raise DatasetNotFoundError('dataset {} not found'.format(dataset))
        return func(self, dataset, *args, **kwargs)
    return inner


def _lazy_load(func):
    """Decorator that computes dataset metadata lazily, whenever a decorated function
    is called. Only computes metadata once for each dataset."""
    def inner(self, dataset, *args, **kwargs):
        if 'meta' not in self._datasets[dataset]:
            self._datasets[dataset]['meta'] = self._load_meta(dataset)
        return func(self, dataset, *args, **kwargs)
    return inner


class TileStore:
    """Stores information about datasets and caches access to tiles."""

    def __init__(self, cfg_path):
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
        options = config.parse_options(cfg)

        self._datasets = self._make_datasets(cfg)
        self._cache = LFUCache(options['tile_cache_size'])

    @staticmethod
    def _make_datasets(cfg):
        """Build datasets from parsed config sections.

        Parameters
        ----------
        cfg_datasets: list of dict
            Each dict represents a dataset config section"""

        datasets = {}
        cfg_datasets = cfg.sections()
        cfg_datasets.remove('options')
        for ds_name in cfg_datasets:
            datasets[ds_name] = config.parse_ds(ds_name, cfg)

        return datasets

    def get_datasets(self):
        return self._datasets.keys()

    @_requires_dataset
    @_lazy_load
    def get_meta(self, dataset):
        return dict(self._datasets[dataset]['meta'])

    @_requires_dataset
    def get_timesteps(self, dataset):
        if not self._datasets[dataset]['timestepped']:
            return []
        return sorted(self._datasets[dataset]['timesteps'].keys())

    @_requires_dataset
    @_lazy_load
    def get_nodata(self, dataset):
        return self._datasets[dataset]['nodata']

    @_requires_dataset
    @_lazy_load
    def get_bounds(self, dataset):
        return self._datasets[dataset]['meta']['wgs_bounds']

    @_requires_dataset
    @_lazy_load
    def get_classes(self, dataset):
        val_range = self._datasets[dataset]['meta']['range']

        if self._datasets[dataset]['categorical']:
            classes = dict(self._datasets[dataset]['classes'])
        else:
            classes = dict(zip(('min', 'max'), val_range))

        return classes

    def _load_meta(self, dataset):
        """ Compute dataset metadata
        Also validate that meta doesn't differ between timesteps.

        Parameters
        ----------
        dataset: str
            Name of dataset

        Returns
        -------
        dict
            Metadata"""

        if self._datasets[dataset]['timestepped']:
            files = self._datasets[dataset]['timesteps'].values()
        else:
            files = [self._datasets[dataset]['file']]

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
        meta['timestepped'] = self._datasets[dataset]['timestepped']

        return frozendict(meta)

    @_requires_dataset
    @_lazy_load
    @cachedmethod(operator.attrgetter('_cache'))
    def tile(self, dataset, tile_x, tile_y, tile_z,
             timestep=None, tilesize=256):
        """Load a requested tile from source.

        Parameters
        ----------
        dataset: str
            name of dataset
        tile_x: int
            Mercator tile X index.
        tile_y: int
            Mercator tile Y index.
        tile_z: int
            Mercator tile ZOOM level.
        timestep: str
            Timestep name if dataset is timestepped
        tilesize: int
            Size in pixels of returned tile image
        """

        ds = self._datasets[dataset]

        if not ds['timestepped'] and timestep:
            raise TileNotFoundError('dataset {} is not timestepped'.format(dataset))
        elif not timestep and ds['timestepped']:
            raise TileNotFoundError('dataset {} is timestepped, but no timestep provided'
                                    .format(dataset))

        if timestep:
            try:
                fname = ds['timesteps'][timestep]
            except KeyError:
                raise TileNotFoundError('no such timestep in dataset {}'.format(dataset))
        else:
            fname = ds['file']

        if not tile_exists(ds['meta']['wgs_bounds'], tile_z, tile_x, tile_y):
            raise TileOutOfBoundsError('Tile {}/{}/{} is outside image bounds'
                                       .format(tile_z, tile_x, tile_y))

        mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
        tile_bounds = mercantile.xy_bounds(mercator_tile)
        tile = self._load_tile(fname, tile_bounds, tilesize)

        alpha_mask = self._alpha_mask(tile, dataset, tilesize)

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

    return mintile.x <= tile_x <= maxtile.x + 1 and mintile.y <= tile_y <= maxtile.y + 1
