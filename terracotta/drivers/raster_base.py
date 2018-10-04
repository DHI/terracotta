"""drivers/raster_base.py

Base class for drivers operating on physical raster files.
"""

from typing import (Any, Union, Mapping, Sequence, Dict, List, Tuple,
                    TypeVar, Optional, cast, TYPE_CHECKING)
from abc import abstractmethod
import contextlib
import operator
import math
import sys
import warnings

import numpy as np
from cachetools import cachedmethod, LRUCache
from affine import Affine

if TYPE_CHECKING:
    from rasterio.io import DatasetReader  # noqa: F401

try:
    from crick import TDigest, SummaryStats
    has_crick = True
except ImportError:
    has_crick = False

from terracotta import get_settings, exceptions, image
from terracotta.drivers.base import requires_connection, Driver
from terracotta.profile import trace

Number = TypeVar('Number', int, float)


class RasterDriver(Driver):
    """Mixin that implements methods to load raster data from disk.

    get_datasets has to return path to raster file as sole dict value.
    """
    TARGET_CRS: str = 'epsg:3857'
    LARGE_RASTER_THRESHOLD: int = 10980 * 10980
    RIO_ENV_KEYS = dict(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR')

    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        settings = get_settings()
        self._raster_cache = LRUCache(settings.RASTER_CACHE_SIZE, getsizeof=sys.getsizeof)
        super().__init__(*args, **kwargs)

    def _key_dict_to_sequence(self, keys: Union[Mapping[str, Any], Sequence[Any]]) -> List[Any]:
        try:
            keys_as_mapping = cast(Mapping[str, Any], keys)
            return [keys_as_mapping[key] for key in self.key_names]
        except TypeError:  # not a mapping
            return list(keys)
        except KeyError as exc:
            raise exceptions.UnknownKeyError('Encountered unknown key') from exc

    @staticmethod
    def _hull_candidate_mask(mask: np.ndarray) -> np.ndarray:
        """Returns a reduced boolean mask to speed up convex hull computations.

        Exploits the fact that only the first and last elements of each row and column
        can contribute to the convex hull of a dataset.
        """
        assert mask.ndim == 2
        assert mask.dtype == np.bool

        nx, ny = mask.shape
        out = np.zeros_like(mask)

        # these operations do not short-circuit, but seems to be the best we can do
        # NOTE: argmax returns 0 if a slice is all True or all False
        first_row = np.argmax(mask, axis=0)
        last_row = nx - 1 - np.argmax(mask[::-1, :], axis=0)
        first_col = np.argmax(mask, axis=1)
        last_col = ny - 1 - np.argmax(mask[:, ::-1], axis=1)

        all_rows = np.arange(nx)
        all_cols = np.arange(ny)

        out[first_row, all_cols] = out[last_row, all_cols] = True
        out[all_rows, first_col] = out[all_rows, last_col] = True

        # filter all-False slices
        out &= mask

        return out

    @staticmethod
    def _compute_image_stats_chunked(dataset: 'DatasetReader',
                                     nodata: Number) -> Optional[Dict[str, Any]]:
        """Loop over chunks and accumulate statistics"""
        from rasterio import features, warp, windows
        from shapely import geometry

        total_count = valid_data_count = 0
        tdigest = TDigest()
        sstats = SummaryStats()
        convex_hull = geometry.Polygon()

        block_windows = [w for _, w in dataset.block_windows(1)]

        for w in block_windows:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='invalid value encountered.*')
                block_data = dataset.read(1, window=w)

            total_count += int(block_data.size)

            valid_data_mask = image.get_valid_mask(block_data, nodata)
            valid_data = block_data[valid_data_mask]

            if valid_data.size == 0:
                continue

            valid_data_count += int(valid_data.size)

            hull_candidates = RasterDriver._hull_candidate_mask(valid_data_mask)
            hull_shapes = (geometry.shape(s) for s, _ in features.shapes(
                np.ones(hull_candidates.shape, 'uint8'),
                mask=hull_candidates,
                transform=windows.transform(w, dataset.transform)
            ))
            convex_hull = geometry.MultiPolygon([convex_hull, *hull_shapes]).convex_hull

            tdigest.update(valid_data)
            sstats.update(valid_data)

        if sstats.count() == 0:
            return None

        convex_hull_wgs = warp.transform_geom(
            dataset.crs, 'epsg:4326', geometry.mapping(convex_hull)
        )

        return {
            'valid_percentage': valid_data_count / total_count * 100,
            'range': (sstats.min(), sstats.max()),
            'mean': sstats.mean(),
            'stdev': sstats.std(),
            'percentiles': tdigest.quantile(np.arange(0.01, 1, 0.01)),
            'convex_hull': convex_hull_wgs
        }

    @staticmethod
    def _compute_image_stats(dataset: 'DatasetReader',
                             nodata: Number) -> Optional[Dict[str, Any]]:
        from rasterio import features, warp
        from shapely import geometry

        raster_data = dataset.read(1)

        valid_data_mask = image.get_valid_mask(raster_data, nodata)
        valid_data = raster_data[valid_data_mask]

        if valid_data.size == 0:
            return None

        hull_candidates = RasterDriver._hull_candidate_mask(valid_data_mask)
        hull_shapes = (geometry.shape(s) for s, _ in features.shapes(
            np.ones(hull_candidates.shape, 'uint8'),
            mask=hull_candidates,
            transform=dataset.transform
        ))
        convex_hull = geometry.MultiPolygon(hull_shapes).convex_hull
        convex_hull_wgs = warp.transform_geom(
            dataset.crs, 'epsg:4326', geometry.mapping(convex_hull)
        )

        return {
            'valid_percentage': valid_data.size / raster_data.size * 100,
            'range': (float(valid_data.min()), float(valid_data.max())),
            'mean': float(valid_data.mean()),
            'stdev': float(valid_data.std()),
            'percentiles': np.percentile(valid_data, np.arange(1, 100)),
            'convex_hull': convex_hull_wgs
        }

    @classmethod
    @trace('compute_metadata')
    def compute_metadata(cls, raster_path: str, *,
                         extra_metadata: Any = None,
                         use_chunks: bool = None) -> Dict[str, Any]:
        """Read given raster file and compute metadata from it.

        This handles most of the heavy lifting during raster ingestion.
        """
        import rasterio
        from rasterio import warp
        from terracotta.cog import validate

        row_data: Dict[str, Any] = {}
        extra_metadata = extra_metadata or {}

        if not validate(raster_path):
            warnings.warn(
                f'Raster file {raster_path} is not a valid cloud-optimized GeoTIFF. '
                'Any interaction with it will be significantly slower. '
                'Consider optimizing it through `terracotta optimize-rasters` before ingestion.',
                exceptions.PerformanceWarning
            )

        with rasterio.Env(**cls.RIO_ENV_KEYS):
            with rasterio.open(raster_path) as src:
                nodata = src.nodata or 0
                bounds = warp.transform_bounds(
                    *[src.crs, 'epsg:4326'] + list(src.bounds), densify_pts=21
                )

                if use_chunks is None:
                    use_chunks = src.width * src.height > RasterDriver.LARGE_RASTER_THRESHOLD

                if use_chunks and not has_crick:
                    warnings.warn(
                        'Processing a large raster file, but crick failed to import. '
                        'Reading whole file into memory instead.', exceptions.PerformanceWarning
                    )
                    use_chunks = False

                if use_chunks:
                    raster_stats = RasterDriver._compute_image_stats_chunked(src, nodata)
                else:
                    raster_stats = RasterDriver._compute_image_stats(src, nodata)

        if raster_stats is None:
            raise ValueError(f'Raster file {raster_path} does not contain any valid data')

        row_data.update(raster_stats)

        row_data['bounds'] = bounds
        row_data['nodata'] = nodata
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
    @trace('calculate_default_transform')
    def _calculate_default_transform(src_crs: Union[Dict[str, str], str],
                                     target_crs: Union[Dict[str, str], str],
                                     width: int,
                                     height: int,
                                     *bounds: Number) -> Tuple[Affine, int, int]:
        """A more stable version of GDAL's default transform.

        Ensures that the number of pixels along the image's shortest diagonal remains
        the same in both CRS, without enforcing square pixels.

        Bounds are in order (west, south, east, north).
        """
        from rasterio import warp, transform

        if len(bounds) != 4:
            raise ValueError('Bounds must contain 4 values')

        # transform image corners to target CRS
        dst_corner_sw, dst_corner_nw, dst_corner_se, dst_corner_ne = (
            list(zip(*warp.transform(
                src_crs, target_crs,
                [bounds[0], bounds[0], bounds[2], bounds[2]],
                [bounds[1], bounds[3], bounds[1], bounds[3]]
            )))
        )

        # determine inner bounding box of corners in target CRS
        dst_corner_bounds = [
            max(dst_corner_sw[0], dst_corner_nw[0]),
            max(dst_corner_sw[1], dst_corner_se[1]),
            min(dst_corner_se[0], dst_corner_ne[0]),
            min(dst_corner_nw[1], dst_corner_ne[1])
        ]

        # compute target resolution
        dst_corner_transform = transform.from_bounds(*dst_corner_bounds, width=width, height=height)
        target_res = (dst_corner_transform.a, dst_corner_transform.e)

        # get transform spanning whole bounds (not just projected corners)
        dst_bounds = warp.transform_bounds(src_crs, target_crs, *bounds)
        dst_width = math.ceil((dst_bounds[2] - dst_bounds[0]) / target_res[0])
        dst_height = math.ceil((dst_bounds[1] - dst_bounds[3]) / target_res[1])
        dst_transform = transform.from_bounds(*dst_bounds, width=dst_width, height=dst_height)

        return dst_transform, dst_width, dst_height

    @cachedmethod(operator.attrgetter('_raster_cache'))
    @requires_connection
    def _get_raster_tile(self, keys: Tuple[str], *,
                         upsampling_method: str,
                         downsampling_method: str,
                         bounds: Tuple[float, float, float, float] = None,
                         tile_size: Tuple[int, int] = (256, 256),
                         nodata: Number = 0,
                         preserve_values: bool = False) -> np.ndarray:
        """Load a raster dataset from a file through rasterio.

        Heavily inspired by mapbox/rio-tiler
        """
        import rasterio
        from rasterio import transform, windows
        from rasterio.vrt import WarpedVRT

        dst_bounds: Tuple[float, float, float, float]

        path = self.get_datasets(dict(zip(self.key_names, keys)))
        assert len(path) == 1
        path = path[keys]

        if preserve_values:
            upsampling_enum = downsampling_enum = self._get_resampling_enum('nearest')
        else:
            upsampling_enum = self._get_resampling_enum(upsampling_method)
            downsampling_enum = self._get_resampling_enum(downsampling_method)

        with contextlib.ExitStack() as es:
            es.enter_context(rasterio.Env(**self.RIO_ENV_KEYS))
            try:
                with trace('open_dataset'):
                    src = es.enter_context(rasterio.open(path))
            except OSError:
                raise IOError('error while reading file {}'.format(path))

            # compute default bounds and transform in target CRS
            dst_transform, dst_width, dst_height = self._calculate_default_transform(
                src.crs, self.TARGET_CRS, src.width, src.height, *src.bounds
            )
            dst_res = (dst_transform.a, dst_transform.e)
            dst_bounds = transform.array_bounds(dst_height, dst_width, dst_transform)

            if bounds is None:
                bounds = dst_bounds

            # update bounds to fit the whole tile
            vrt_bounds = [
                min(dst_bounds[0], bounds[0]),
                min(dst_bounds[1], bounds[1]),
                max(dst_bounds[2], bounds[2]),
                max(dst_bounds[3], bounds[3])
            ]

            # re-compute shape and transform with updated bounds
            vrt_width = math.ceil((vrt_bounds[2] - vrt_bounds[0]) / dst_res[0])
            vrt_height = math.ceil((vrt_bounds[1] - vrt_bounds[3]) / dst_res[1])
            vrt_transform = transform.from_bounds(*vrt_bounds, width=vrt_width, height=vrt_height)

            # construct VRT
            vrt = es.enter_context(
                WarpedVRT(
                    src, crs=self.TARGET_CRS, resampling=upsampling_enum, init_dest_nodata=True,
                    src_nodata=nodata, nodata=nodata, transform=vrt_transform, width=vrt_width,
                    height=vrt_height
                )
            )

            # compute output window
            out_window = windows.from_bounds(*bounds, transform=vrt_transform)

            # prevent expensive loads of very sparse data
            window_ratio = dst_width / out_window.width * dst_height / out_window.height

            if window_ratio < 0.001:
                raise exceptions.TileOutOfBoundsError('data covers less than 0.1% of tile')

            # determine whether we are upsampling or downsampling
            if window_ratio > 1:
                resampling_enum = upsampling_enum
            else:
                resampling_enum = downsampling_enum

            # read data
            with warnings.catch_warnings(), trace('read_from_vrt'):
                warnings.filterwarnings('ignore', message='invalid value encountered.*')
                arr = vrt.read(
                    1, resampling=resampling_enum, window=out_window, out_shape=tile_size
                )

            assert arr.shape == tile_size, arr.shape

        return arr

    @trace('get_raster_tile')
    def get_raster_tile(self, keys: Union[Sequence[str], Mapping[str, str]], *,
                        bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = (256, 256),
                        preserve_values: bool = False) -> np.ndarray:
        """Load tile with given keys or metadata"""
        # make sure all arguments are hashable
        settings = get_settings()
        key_sequence = self._key_dict_to_sequence(keys)
        nodata = self.get_metadata(keys)['nodata']
        return self._get_raster_tile(
            tuple(key_sequence),
            bounds=tuple(bounds) if bounds else None,
            tile_size=tuple(tile_size),
            nodata=nodata,
            preserve_values=preserve_values,
            upsampling_method=settings.UPSAMPLING_METHOD,
            downsampling_method=settings.DOWNSAMPLING_METHOD
        )
