"""drivers/base.py

Base class and mixins for drivers.
"""

from abc import ABC, abstractmethod
from typing import Callable, Mapping, Any, Tuple, Sequence, Dict, Union, List
import sys
import operator
import math
import warnings
import functools
import contextlib

from cachetools import cachedmethod, LRUCache
import numpy as np

from terracotta import get_settings, exceptions


def requires_connection(fun: Callable) -> Callable:
    @functools.wraps(fun)
    def inner(self: Driver, *args: Any, **kwargs: Any) -> Any:
        with self.connect():
            return fun(self, *args, **kwargs)
    return inner


class Driver(ABC):
    """Abstract base class for all data backends.

    Defines a common interface for all handlers.
    """
    available_keys: Tuple[str]

    @abstractmethod
    def __init__(self, url_or_path: str) -> None:
        pass

    @abstractmethod
    def create(self, *args: Any, **kwargs: Any) -> None:
        """Create a new, empty data storage"""
        pass

    @abstractmethod
    def connect(self) -> contextlib.AbstractContextManager:
        """Context manager to connect to a given database and clean up on exit."""
        pass

    @abstractmethod
    def get_datasets(self, where: Mapping[str, str] = None) -> Dict[Tuple[str, ...], Any]:
        """Get all known dataset key combinations matching the given pattern (all if not given).

        Values are a handle to retrieve data.
        """
        pass

    @abstractmethod
    def get_metadata(self, keys: Union[Sequence[str], Mapping[str, str]]) -> Dict[str, Any]:
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
    def get_raster_tile(self, keys: Union[Sequence[str], Mapping[str, str]], *,
                        bounds: Sequence[float] = None,
                        tilesize: Sequence[int] = (256, 256)) -> np.ndarray:
        """Get raster tile as a NumPy array for given keys."""
        pass

    @abstractmethod
    def insert(self, *args: Any, **kwargs: Any) -> None:
        """Register a new dataset. Used to populate data storage."""
        pass


class RasterDriver(Driver):
    """Mixin that implements methods to load raster data from disk.

    get_datasets has to return path to raster file as sole dict value.
    """

    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        settings = get_settings()
        self._raster_cache = LRUCache(settings.RASTER_CACHE_SIZE, getsizeof=sys.getsizeof)
        super(RasterDriver, self).__init__(*args, **kwargs)

    def _key_dict_to_sequence(self, keys: Union[Mapping[str, Any], Sequence[Any]]
                              ) -> List[Any]:
        try:
            return [keys[key] for key in self.available_keys]  # type: ignore
        except TypeError:  # not a mapping
            return list(keys)
        except KeyError as exc:
            raise exceptions.UnknownKeyError('Encountered unknown key') from exc

    @staticmethod
    def _compute_metadata(raster_path: str,
                          extra_metadata: Mapping[str, Any] = None) -> Mapping[str, Any]:
        """Read given raster file and compute metadata from it"""
        import rasterio
        from rasterio.warp import transform_bounds

        row_data = {}
        extra_metadata = extra_metadata or {}

        with rasterio.open(raster_path) as src:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='invalid value encountered.*')
                raster_data = src.read(1)
            nodata = src.nodata or 0
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
        row_data['metadata'] = extra_metadata
        return row_data

    @cachedmethod(operator.attrgetter('_raster_cache'))
    @requires_connection
    def _get_raster_tile(self, keys: Tuple[str], *,
                         bounds: Tuple[float, float, float, float] = None,
                         tilesize: Tuple[int, int] = (256, 256)) -> np.ndarray:
        """Load a raster dataset from a file through rasterio.

        Heavily inspired by mapbox/rio-tiler
        """
        import rasterio
        from rasterio import transform, warp
        from rasterio.vrt import WarpedVRT
        from rasterio.enums import Resampling

        path = self.get_datasets(dict(zip(self.available_keys, keys)))
        assert len(path) == 1
        path = path[keys]

        target_crs = 'epsg:3857'
        resampling = Resampling.nearest

        with contextlib.ExitStack() as es:
            try:
                src = es.enter_context(rasterio.open(path))
            except OSError:
                raise IOError('error while reading file {}'.format(path))

            dst_transform, _, _ = warp.calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds
            )

            if bounds is not None:
                w, s, e, n = bounds
            else:
                w, s, e, n = src.bounds

            vrt_width = math.ceil((e - w) / dst_transform.a)
            vrt_height = math.ceil((s - n) / dst_transform.e)
            vrt_transform = transform.from_bounds(w, s, e, n, vrt_width, vrt_height)
            vrt = es.enter_context(
                WarpedVRT(
                    src, crs=target_crs, resampling=resampling,
                    transform=vrt_transform, width=vrt_width, height=vrt_height
                )
            )

            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='invalid value encountered.*')
                arr = vrt.read(1, out_shape=tilesize, resampling=resampling)

        return arr

    def get_raster_tile(self, keys: Union[Sequence[str], Mapping[str, str]], *,
                        bounds: Sequence[float] = None,
                        tilesize: Sequence[int] = (256, 256)) -> np.ndarray:
        """Load tile with given keys or metadata"""
        # make sure all arguments are hashable
        _keys = self._key_dict_to_sequence(keys)
        return self._get_raster_tile(tuple(_keys), bounds=tuple(bounds) if bounds else None,
                                     tilesize=tuple(tilesize))
