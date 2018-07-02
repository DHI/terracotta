"""base.py

Base class and mixins for data handlers.
"""

from abc import ABC, abstractmethod
from typing import Callable, Mapping, Any, Tuple, Optional, Sequence, List
import operator
import functools

from cachetools import cachedmethod, LRUCache
import numpy as np

from terracotta import exceptions, settings


def requires_connection(fun: Callable) -> Callable:
    @functools.wraps(fun)
    def inner(self, *args, **kwargs):
        if self.conn is None:
            with self.connect():
                return fun(self, *args, **kwargs)
        return fun(self, *args, **kwargs)
    return inner


class Driver(ABC):
    """Abstract base class for all data backends.

    Defines a common interface for all handlers.
    """
    available_keys: Optional[Tuple] = None

    @abstractmethod
    def __init__(self, url_or_path: str, *args, **kwargs):
        pass

    @abstractmethod
    def create(self, *args, **kwargs):
        """Create a new, empty data storage"""
        pass

    @abstractmethod
    def connect(self):
        """Context manager to connect to a given database and clean up on exit."""
        pass

    @abstractmethod
    def get_datasets(self, where: Mapping[str, str] = None) -> List[Mapping[str, Any]]:
        """Get all known dataset key combinations matching the given pattern (all if not given).

        Values are a handle to retrieve data.
        """
        pass

    @abstractmethod
    def get_metadata(self, keys: Sequence[str]) -> Mapping[str, Any]:
        """Return all stored metadata for given keys.

        Metadata has to contain the following keys:
          - range: global minimum and maximum value in dataset
          - bounds: physical bounds covered by dataset
          - nodata: data value denoting missing or invalid data
          - percentiles: array of pre-computed percentiles in range(1, 100)
          - mean: global mean
          - stdev: global standard deviation
          - metadata: any additional client-relevant metadata
        """
        pass

    @abstractmethod
    def get_raster_tile(self, keys: Sequence[str], *, bounds: Sequence[float] = None,
                        tilesize: Sequence[int] = (256, 256)) -> np.ndarray:
        """Get raster tile as a NumPy array for given keys."""
        pass

    @abstractmethod
    def insert(self, *args, **kwargs):
        """Register a new dataset. Used to populate data storage."""
        pass


class RasterDriver(Driver):
    """Mixin that implements methods to load raster data from disk.

    get_datasets has to return path to raster file as sole dict value.
    """

    @abstractmethod
    def __init__(self, *args, **kwargs):
        self._raster_cache = LRUCache(settings.CACHE_SIZE)

    @staticmethod
    def _compute_metadata(raster_path: str,
                          extra_metadata: Mapping[str, Any] = None) -> Mapping[str, Any]:
        """Read given raster file and compute metadata from it"""
        import json
        import numpy as np
        import rasterio
        from rasterio.warp import transform_bounds

        row_data = {}
        extra_metadata = extra_metadata or {}

        with rasterio.open(raster_path) as src:
            raster_data = src.read(1)
            nodata = src.nodata
            bounds = transform_bounds(*[src.crs, 'epsg:4326'] + list(src.bounds), densify_pts=21)

        row_data['bounds'] = bounds
        row_data['nodata'] = nodata
        if np.isnan(nodata):
            valid_data = raster_data[np.isfinite(raster_data)]
        else:
            valid_data = raster_data[raster_data != nodata]
        row_data['range'] = (float(valid_data.min()), float(valid_data.max()))
        row_data['mean'] = float(valid_data.mean())
        row_data['stdev'] = float(valid_data.std())
        row_data['percentiles'] = np.percentile(valid_data, np.arange(1, 100))
        row_data['metadata'] = json.dumps(extra_metadata)
        return row_data

    @cachedmethod(operator.attrgetter('_raster_cache'))
    def _get_raster_tile(self, keys: Tuple[str], *, bounds: Tuple[float] = None,
                         tilesize: Tuple[int] = (256, 256)) -> np.ndarray:
        import rasterio
        from rasterio.vrt import WarpedVRT
        from rasterio.enums import Resampling

        path = self.get_datasets(dict(zip(self.available_keys, keys)))
        assert len(path) == 1
        path = path[keys]
        try:
            with rasterio.open(path) as src, WarpedVRT(src, dst_crs='epsg:3857',
                                                       resampling=Resampling.bilinear) as vrt:
                    window = vrt.window(*bounds) if bounds is not None else None
                    arr = vrt.read(
                        1,
                        window=window,
                        out_shape=tilesize,
                        boundless=True
                    )
        except OSError:
            raise exceptions.TileNotFoundError('error while reading file {}'.format(path))

        return arr

    def get_raster_tile(self, keys: Sequence[str], *, bounds: Sequence[float] = None,
                        tilesize: Tuple[int] = (256, 256)) -> np.ndarray:
        """Load tile with given keys or metadata"""
        # make sure all arguments are hashable
        return self._get_raster_tile(tuple(keys), bounds=tuple(bounds) if bounds else None,
                                     tilesize=tuple(tilesize))
