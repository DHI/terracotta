"""drivers/base.py

Base class and mixins for drivers.
"""

from abc import ABC, abstractmethod
from typing import Callable, Mapping, Any, Tuple, Sequence, Dict, Union, List, TypeVar
import sys
import operator
import math
import warnings
import functools
import contextlib

from cachetools import cachedmethod, LRUCache
import numpy as np

from terracotta import get_settings, exceptions

Number = TypeVar('Number', int, float)


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
                        tilesize: Sequence[int] = (256, 256),
                        nodata: Number = 0) -> np.ndarray:
        """Get raster tile as a NumPy array for given keys."""
        pass

    @staticmethod
    @abstractmethod
    def compute_metadata(data: Any, *,
                         extra_metadata: Any = None) -> Dict[str, Any]:
        """Compute metadata for a given input file."""
        pass

    @abstractmethod
    def insert(self, *args: Any,
               metadata: Mapping[str, Any] = None,
               skip_metadata: bool = False,
               **kwargs: Any) -> None:
        """Register a new dataset. Used to populate data storage."""
        pass

    @abstractmethod
    def delete(self, keys: Union[Sequence[str], Mapping[str, str]]) -> None:
        """Remove a dataset from metadata storage."""
        pass


class RasterDriver(Driver):
    """Mixin that implements methods to load raster data from disk.

    get_datasets has to return path to raster file as sole dict value.
    """
    MAX_TRANSFORM_SIZE: int = 10980

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
    def compute_metadata(raster_path: str, *,
                         extra_metadata: Any = None) -> Dict[str, Any]:
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

        valid_data = raster_data[np.isfinite(raster_data)]
        if not np.isnan(nodata):
            valid_data = valid_data[valid_data != nodata]

        if valid_data.size == 0:
            raise ValueError(f'Raster file {raster_path} does not contain any valid data')

        row_data['range'] = (float(valid_data.min()), float(valid_data.max()))
        row_data['mean'] = float(valid_data.mean())
        row_data['stdev'] = float(valid_data.std())
        row_data['percentiles'] = np.percentile(valid_data, np.arange(1, 100))
        row_data['metadata'] = extra_metadata
        return row_data

    @staticmethod
    def _get_resampling_enum(method: str) -> Any:
        from rasterio.enums import Resampling
        if method == 'nearest':
            return Resampling.nearest

        if method == 'linear':
            return Resampling.bilinear

        if method == 'cubic':
            return Resampling.cubic

        if method == 'average':
            return Resampling.average

        raise ValueError(f'unknown resampling method {method}')

    @staticmethod
    def _safe_default_transform(dataset, crs):
        """Work around memory issues when computing default transform for huge rasters"""
        from affine import Affine
        from rasterio.warp import calculate_default_transform

        max_size = RasterDriver.MAX_TRANSFORM_SIZE
        height_scale = max(dataset.height // max_size, 1)
        width_scale = max(dataset.width // max_size, 1)

        dst_transform, dst_width, dst_height = calculate_default_transform(
            dataset.crs, crs,
            dataset.width // width_scale,
            dataset.height // height_scale,
            *dataset.bounds
        )

        scale = Affine.scale(width_scale, height_scale)
        print(scale)
        dst_transform *= ~scale
        dst_width, dst_height = scale * (dst_width, dst_height)

        return dst_transform, dst_width, dst_height

    @cachedmethod(operator.attrgetter('_raster_cache'))
    @requires_connection
    def _get_raster_tile(self, keys: Tuple[str], *,
                         bounds: Tuple[float, float, float, float] = None,
                         tilesize: Tuple[int, int] = (256, 256),
                         nodata: Number = 0) -> np.ndarray:
        """Load a raster dataset from a file through rasterio.

        Heavily inspired by mapbox/rio-tiler
        """
        import rasterio
        from rasterio import transform, windows
        from rasterio.vrt import WarpedVRT

        settings = get_settings()

        path = self.get_datasets(dict(zip(self.available_keys, keys)))
        assert len(path) == 1
        path = path[keys]

        target_crs = 'epsg:3857'
        resampling_method = settings.RESAMPLING_METHOD
        resampling_enum = self._get_resampling_enum(resampling_method)

        with contextlib.ExitStack() as es:
            try:
                src = es.enter_context(rasterio.open(path))
            except OSError:
                raise IOError('error while reading file {}'.format(path))

            # compute default bounds and transform in target CRS
            dst_transform, dst_width, dst_height = self._safe_default_transform(src, target_crs)
            dst_bounds = transform.array_bounds(dst_height, dst_width, dst_transform)
            print(dst_transform, dst_width, dst_height)

            # update bounds to fit the whole tile
            if bounds is not None:
                w_vrt = min(dst_bounds[0], bounds[0])
                s_vrt = min(dst_bounds[1], bounds[1])
                e_vrt = max(dst_bounds[2], bounds[2])
                n_vrt = max(dst_bounds[3], bounds[3])
            else:
                w_vrt, s_vrt, e_vrt, n_vrt = dst_bounds

            # re-compute shape and transform with updated bounds
            vrt_width = math.ceil((e_vrt - w_vrt) / dst_transform.a)
            vrt_height = math.ceil((s_vrt - n_vrt) / dst_transform.e)
            vrt_transform = transform.from_bounds(w_vrt, s_vrt, e_vrt, n_vrt, vrt_width, vrt_height)

            # construct VRT
            vrt = es.enter_context(
                WarpedVRT(
                    src, crs=target_crs, resampling=resampling_enum, init_dest_nodata=True,
                    src_nodata=nodata, nodata=nodata, transform=vrt_transform, width=vrt_width,
                    height=vrt_height
                )
            )

            # only read in given bounds from VRT
            if bounds is None:
                window_bounds = dst_bounds
            else:
                window_bounds = bounds

            # compute output window
            out_window = windows.from_bounds(*window_bounds, transform=vrt_transform)

            # prevent expensive loads of very sparse data
            window_ratio = dst_width / out_window.width * dst_height / out_window.height

            if window_ratio < 0.001:
                raise exceptions.TileOutOfBoundsError('data covers less than 0.1% of tile')

            # read data
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='invalid value encountered.*')
                arr = vrt.read(1, resampling=resampling_enum, window=out_window, out_shape=tilesize)

            assert arr.shape == tilesize, arr.shape

        return arr

    def get_raster_tile(self, keys: Union[Sequence[str], Mapping[str, str]], *,
                        bounds: Sequence[float] = None,
                        tilesize: Sequence[int] = (256, 256),
                        nodata: Number = 0) -> np.ndarray:
        """Load tile with given keys or metadata"""
        # make sure all arguments are hashable
        _keys = self._key_dict_to_sequence(keys)
        return self._get_raster_tile(
            tuple(_keys),
            bounds=tuple(bounds) if bounds else None,
            tilesize=tuple(tilesize),
            nodata=nodata
        )
