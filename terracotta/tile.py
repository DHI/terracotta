import operator

from cachetools import LFUCache, cachedmethod
import mercantile
import rasterio
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling


DEFAULT_CACHE_SIZE = 256000000 # 256MB


class TileNotFoundError(Exception):
    pass


class TileStore:
    """Stores information about datasets and caches access to tiles."""

    def __init__(self, datasets, cache_size=DEFAULT_CACHE_SIZE):
        self.cache = LFUCache(cache_size)
        self.datasets = datasets

    @cachedmethod(operator.attrgetter('cache'))
    def tile(tile_x, tile_y, tile_z, dataset, timestep=None):
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
            dataset = self.datasets[dataset]
        except KeyError:
            raise TileNotFoundError('no such dataset {}'.format(dataset))

        if not dataset['timestepped'] and timestep:
            raise TileNotFoundError('dataset {} is not timestepped'.format(dataset))

        if timestep:
            try:
                fname = dataset['timesteps'][timestep]
            except KeyError:
                raise TileNotFoundError('no such timestep in dataset {}'.format(dataset))
        else:
            fname = dataset['filename']

        if not tile_exists(dataset['wgs_bound'], tile_z, tile_x, tile_y):
            raise TileNotFoundError('Tile {}/{}/{} is outside image bounds'
                                    .format(tile_z, tile_x, tile_y))

        mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
        tile_bounds = mercantile.xy_bounds(mercator_tile)

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
                with WarpedVRT(src, dst_crs='epsg:3857') as vrt:
                    window = vrt.window(*bounds)
                    arr_transform = vrt.window_transform(window)
                    arr = vrt.read(window=window)
        except OSError:
            raise TileNotFoundError('error while reading file {}'.format(path))

        return arr


def tile_exists(bounds, tile_z, tile_x, tile_y):
    """Check if a mercatile tile is inside a given bounds
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
