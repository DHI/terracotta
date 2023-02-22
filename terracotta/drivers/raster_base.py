"""drivers/raster_base.py

Base class for drivers operating on physical raster files.
"""

from typing import (Any, Callable, Union, Mapping, Sequence, Dict, List, Tuple,
                    TypeVar, Optional, cast, TYPE_CHECKING)
from abc import abstractmethod
from concurrent.futures import Future, Executor, ProcessPoolExecutor, ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool

import contextlib
import functools
import logging
import warnings
import threading

import numpy as np

if TYPE_CHECKING:  # pragma: no cover
    from rasterio.io import DatasetReader  # noqa: F401

try:
    from crick import TDigest, SummaryStats
    has_crick = True
except ImportError:  # pragma: no cover
    has_crick = False

from terracotta import get_settings, exceptions
from terracotta.cache import CompressedLFUCache
from terracotta.drivers.base import requires_connection, Driver
from terracotta.profile import trace

Number = TypeVar('Number', int, float)

logger = logging.getLogger(__name__)

context = threading.local()
context.executor = None


def create_executor() -> Executor:
    settings = get_settings()

    if not settings.USE_MULTIPROCESSING:
        return ThreadPoolExecutor(max_workers=1)

    executor: Executor

    try:
        # this fails on architectures without /dev/shm
        executor = ProcessPoolExecutor(max_workers=3)
    except OSError:
        # fall back to serial evaluation
        warnings.warn(
            'Multiprocessing is not available on this system. '
            'Falling back to serial execution.'
        )
        executor = ThreadPoolExecutor(max_workers=1)

    return executor


def submit_to_executor(task: Callable[..., Any]) -> Future:
    if context.executor is None:
        context.executor = create_executor()

    try:
        future = context.executor.submit(task)
    except BrokenProcessPool:
        # re-create executor and try again
        logger.warn('Re-creating broken process pool')
        context.executor = create_executor()
        future = context.executor.submit(task)

    return future


class RasterDriver(Driver):
    """Mixin that implements methods to load raster data from disk.

    get_datasets has to return path to raster file as sole dict value.
    """
    _TARGET_CRS: str = 'epsg:3857'
    _LARGE_RASTER_THRESHOLD: int = 10980 * 10980
    _RIO_ENV_KEYS = dict(
        GDAL_TIFF_INTERNAL_MASK=True,
        GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'
    )

    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        settings = get_settings()
        self._raster_cache = CompressedLFUCache(
            settings.RASTER_CACHE_SIZE,
            compression_level=settings.RASTER_CACHE_COMPRESS_LEVEL
        )
        self._cache_lock = threading.RLock()
        super().__init__(*args, **kwargs)

    # specify signature and docstring for insert
    @abstractmethod
    def insert(self,  # type: ignore
               keys: Union[Sequence[str], Mapping[str, str]],
               filepath: str, *,
               metadata: Mapping[str, Any] = None,
               skip_metadata: bool = False,
               override_path: str = None) -> None:
        """Insert a raster file into the database.

        Arguments:

            keys: Keys identifying the new dataset. Can either be given as a sequence of key
                values, or as a mapping ``{key_name: key_value}``.
            filepath: Path to the GDAL-readable raster file.
            metadata: If not given (default), call :meth:`compute_metadata` with default arguments
                to compute raster metadata. Otherwise, use the given values. This can be used to
                decouple metadata computation from insertion, or to use the optional arguments
                of :meth:`compute_metadata`.
            skip_metadata: Do not compute any raster metadata (will be computed during the first
                request instead). Use sparingly; this option has a detrimental result on the end
                user experience and might lead to surprising results. Has no effect if ``metadata``
                is given.
            override_path: Override the path to the raster file in the database. Use this option if
                you intend to copy the data somewhere else after insertion (e.g. when moving files
                to a cloud storage later on).

        """
        pass

    # specify signature and docstring for get_datasets
    @abstractmethod
    def get_datasets(self, where: Mapping[str, Union[str, List[str]]] = None,
                     page: int = 0, limit: int = None) -> Dict[Tuple[str, ...], str]:
        """Retrieve keys and file paths of datasets.

        Arguments:

            where: Constraints on returned datasets in the form ``{key_name: allowed_key_value}``.
                Returns all datasets if not given (default).
            page: Current page of results. Has no effect if ``limit`` is not given.
            limit: If given, return at most this many datasets. Unlimited by default.


        Returns:

            :class:`dict` containing
            ``{(key_value1, key_value2, ...): raster_file_path}``

        Example:

            >>> import terracotta as tc
            >>> driver = tc.get_driver('tc.sqlite')
            >>> driver.get_datasets()
            {
                ('reflectance', '20180101', 'B04'): 'reflectance_20180101_B04.tif',
                ('reflectance', '20180102', 'B04'): 'reflectance_20180102_B04.tif',
            }
            >>> driver.get_datasets({'date': '20180101'})
            {('reflectance', '20180101', 'B04'): 'reflectance_20180101_B04.tif'}

        """
        pass

    def _key_dict_to_sequence(self, keys: Union[Mapping[str, Any], Sequence[Any]]) -> List[Any]:
        """Convert {key_name: key_value} to [key_value] with the correct key order."""
        try:
            keys_as_mapping = cast(Mapping[str, Any], keys)
            return [keys_as_mapping[key] for key in self.key_names]
        except TypeError:  # not a mapping
            return list(keys)
        except KeyError as exc:
            raise exceptions.InvalidKeyError('Encountered unknown key') from exc

    @staticmethod
    def _hull_candidate_mask(mask: np.ndarray) -> np.ndarray:
        """Returns a reduced boolean mask to speed up convex hull computations.

        Exploits the fact that only the first and last elements of each row and column
        can contribute to the convex hull of a dataset.
        """
        assert mask.ndim == 2
        assert mask.dtype == np.bool_

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
    def _compute_image_stats_chunked(dataset: 'DatasetReader') -> Optional[Dict[str, Any]]:
        """Compute statistics for the given rasterio dataset by looping over chunks."""
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
                block_data = dataset.read(1, window=w, masked=True)

            # handle NaNs for float rasters
            block_data = np.ma.masked_invalid(block_data, copy=False)

            total_count += int(block_data.size)
            valid_data = block_data.compressed()

            if valid_data.size == 0:
                continue

            valid_data_count += int(valid_data.size)

            if np.any(block_data.mask):
                hull_candidates = RasterDriver._hull_candidate_mask(~block_data.mask)
                hull_shapes = [geometry.shape(s) for s, _ in features.shapes(
                    np.ones(hull_candidates.shape, 'uint8'),
                    mask=hull_candidates,
                    transform=windows.transform(w, dataset.transform)
                )]
            else:
                w, s, e, n = windows.bounds(w, dataset.transform)
                hull_shapes = [geometry.Polygon([(w, s), (e, s), (e, n), (w, n)])]
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
                             max_shape: Sequence[int] = None) -> Optional[Dict[str, Any]]:
        """Compute statistics for the given rasterio dataset by reading it into memory."""
        from rasterio import features, warp, transform
        from shapely import geometry

        out_shape = (dataset.height, dataset.width)

        if max_shape is not None:
            out_shape = (
                min(max_shape[0], out_shape[0]),
                min(max_shape[1], out_shape[1])
            )

        data_transform = transform.from_bounds(
            *dataset.bounds, height=out_shape[0], width=out_shape[1]
        )
        raster_data = dataset.read(1, out_shape=out_shape, masked=True)

        if dataset.nodata is not None:
            # nodata values might slip into output array if out_shape < dataset.shape
            raster_data = np.ma.masked_equal(raster_data, dataset.nodata, copy=False)

        # handle NaNs for float rasters
        raster_data = np.ma.masked_invalid(raster_data, copy=False)

        valid_data = raster_data.compressed()

        if valid_data.size == 0:
            return None

        if np.any(raster_data.mask):
            hull_candidates = RasterDriver._hull_candidate_mask(~raster_data.mask)
            hull_shapes = (geometry.shape(s) for s, _ in features.shapes(
                np.ones(hull_candidates.shape, 'uint8'),
                mask=hull_candidates,
                transform=data_transform
            ))
            convex_hull = geometry.MultiPolygon(hull_shapes).convex_hull
        else:
            # no masked entries -> convex hull == dataset bounds
            w, s, e, n = dataset.bounds
            convex_hull = geometry.Polygon([(w, s), (e, s), (e, n), (w, n)])

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
    def compute_metadata(cls, raster_path: str, *,  # type: ignore[override]  # noqa: F821
                         extra_metadata: Any = None,
                         use_chunks: bool = None,
                         max_shape: Sequence[int] = None) -> Dict[str, Any]:
        """Read given raster file and compute metadata from it.

        This handles most of the heavy lifting during raster ingestion. The returned metadata can
        be passed directly to :meth:`insert`.

        Arguments:

            raster_path: Path to GDAL-readable raster file
            extra_metadata: Any additional metadata to attach to the dataset. Will be
                JSON-serialized and returned verbatim by :meth:`get_metadata`.
            use_chunks: Whether to process the image in chunks (slower, but uses less memory).
                If not given, use chunks for large images only.
            max_shape: Gives the maximum number of pixels used in each dimension to compute
                metadata. Setting this to a relatively small size such as ``(1024, 1024)`` will
                result in much faster metadata computation for large images, at the expense of
                inaccurate results.

        """
        import rasterio
        from rasterio import warp
        from terracotta.cog import validate

        row_data: Dict[str, Any] = {}
        extra_metadata = extra_metadata or {}

        if max_shape is not None and len(max_shape) != 2:
            raise ValueError('max_shape argument must contain 2 values')

        if use_chunks and max_shape is not None:
            raise ValueError('Cannot use both use_chunks and max_shape arguments')

        with rasterio.Env(**cls._RIO_ENV_KEYS):
            if not validate(raster_path):
                warnings.warn(
                    f'Raster file {raster_path} is not a valid cloud-optimized GeoTIFF. '
                    'Any interaction with it will be significantly slower. Consider optimizing '
                    'it through `terracotta optimize-rasters` before ingestion.',
                    exceptions.PerformanceWarning, stacklevel=3
                )

            with rasterio.open(raster_path) as src:
                if src.nodata is None and not cls._has_alpha_band(src):
                    warnings.warn(
                        f'Raster file {raster_path} does not have a valid nodata value, '
                        'and does not contain an alpha band. No data will be masked.'
                    )

                bounds = warp.transform_bounds(
                    src.crs, 'epsg:4326', *src.bounds, densify_pts=21
                )

                if use_chunks is None and max_shape is None:
                    use_chunks = src.width * src.height > RasterDriver._LARGE_RASTER_THRESHOLD

                    if use_chunks:
                        logger.debug(
                            f'Computing metadata for file {raster_path} using more than '
                            f'{RasterDriver._LARGE_RASTER_THRESHOLD // 10**6}M pixels, iterating '
                            'over chunks'
                        )

                if use_chunks and not has_crick:
                    warnings.warn(
                        'Processing a large raster file, but crick failed to import. '
                        'Reading whole file into memory instead.', exceptions.PerformanceWarning
                    )
                    use_chunks = False

                if use_chunks:
                    raster_stats = RasterDriver._compute_image_stats_chunked(src)
                else:
                    raster_stats = RasterDriver._compute_image_stats(src, max_shape)

        if raster_stats is None:
            raise ValueError(f'Raster file {raster_path} does not contain any valid data')

        row_data.update(raster_stats)

        row_data['bounds'] = bounds
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
    def _has_alpha_band(src: 'DatasetReader') -> bool:
        from rasterio.enums import MaskFlags, ColorInterp
        return (
            any([MaskFlags.alpha in flags for flags in src.mask_flag_enums])
            or ColorInterp.alpha in src.colorinterp
        )

    @classmethod
    @trace('get_raster_tile')
    def _get_raster_tile(cls, path: str, *,
                         reprojection_method: str,
                         resampling_method: str,
                         tile_bounds: Tuple[float, float, float, float] = None,
                         tile_size: Tuple[int, int] = (256, 256),
                         preserve_values: bool = False) -> np.ma.MaskedArray:
        """Load a raster dataset from a file through rasterio.

        Heavily inspired by mapbox/rio-tiler
        """
        import rasterio
        from rasterio import transform, windows, warp
        from rasterio.vrt import WarpedVRT
        from affine import Affine

        dst_bounds: Tuple[float, float, float, float]

        if preserve_values:
            reproject_enum = resampling_enum = cls._get_resampling_enum('nearest')
        else:
            reproject_enum = cls._get_resampling_enum(reprojection_method)
            resampling_enum = cls._get_resampling_enum(resampling_method)

        with contextlib.ExitStack() as es:
            es.enter_context(rasterio.Env(**cls._RIO_ENV_KEYS))
            try:
                with trace('open_dataset'):
                    src = es.enter_context(rasterio.open(path))
            except OSError:
                raise IOError('error while reading file {}'.format(path))

            # compute buonds in target CRS
            dst_bounds = warp.transform_bounds(src.crs, cls._TARGET_CRS, *src.bounds)

            if tile_bounds is None:
                tile_bounds = dst_bounds

            # prevent loads of very sparse data
            cover_ratio = (
                (dst_bounds[2] - dst_bounds[0]) / (tile_bounds[2] - tile_bounds[0])
                * (dst_bounds[3] - dst_bounds[1]) / (tile_bounds[3] - tile_bounds[1])
            )

            if cover_ratio < 0.01:
                raise exceptions.TileOutOfBoundsError('dataset covers less than 1% of tile')

            # compute suggested resolution in target CRS
            dst_transform, _, _ = warp.calculate_default_transform(
                src.crs, cls._TARGET_CRS, src.width, src.height, *src.bounds
            )
            dst_res = (abs(dst_transform.a), abs(dst_transform.e))

            # make sure VRT resolves the entire tile
            tile_transform = transform.from_bounds(*tile_bounds, *tile_size)
            tile_res = (abs(tile_transform.a), abs(tile_transform.e))

            if tile_res[0] < dst_res[0] or tile_res[1] < dst_res[1]:
                dst_res = tile_res
                resampling_enum = cls._get_resampling_enum('nearest')

            # pad tile bounds to prevent interpolation artefacts
            num_pad_pixels = 2

            # compute tile VRT shape and transform
            dst_width = max(1, round((tile_bounds[2] - tile_bounds[0]) / dst_res[0]))
            dst_height = max(1, round((tile_bounds[3] - tile_bounds[1]) / dst_res[1]))
            vrt_transform = (
                transform.from_bounds(*tile_bounds, width=dst_width, height=dst_height)
                * Affine.translation(-num_pad_pixels, -num_pad_pixels)
            )
            vrt_height, vrt_width = dst_height + 2 * num_pad_pixels, dst_width + 2 * num_pad_pixels

            # remove padding in output
            out_window = windows.Window(
                col_off=num_pad_pixels, row_off=num_pad_pixels, width=dst_width, height=dst_height
            )

            # construct VRT
            vrt = es.enter_context(
                WarpedVRT(
                    src, crs=cls._TARGET_CRS, resampling=reproject_enum,
                    transform=vrt_transform, width=vrt_width, height=vrt_height,
                    add_alpha=not cls._has_alpha_band(src)
                )
            )

            # read data
            with warnings.catch_warnings(), trace('read_from_vrt'):
                warnings.filterwarnings('ignore', message='invalid value encountered.*')
                tile_data = vrt.read(
                    1, resampling=resampling_enum, window=out_window, out_shape=tile_size
                )

                # assemble alpha mask
                mask_idx = vrt.count
                mask = vrt.read(mask_idx, window=out_window, out_shape=tile_size) == 0

                if src.nodata is not None:
                    mask |= tile_data == src.nodata

        return np.ma.masked_array(tile_data, mask=mask)

    # return type has to be Any until mypy supports conditional return types
    @requires_connection
    def get_raster_tile(self,
                        keys: Union[Sequence[str], Mapping[str, str]], *,
                        tile_bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = None,
                        preserve_values: bool = False,
                        asynchronous: bool = False) -> Any:
        # This wrapper handles cache interaction and asynchronous tile retrieval.
        # The real work is done in _get_raster_tile.

        future: Future[np.ma.MaskedArray]
        result: np.ma.MaskedArray

        settings = get_settings()
        key_tuple = tuple(self._key_dict_to_sequence(keys))
        datasets = self.get_datasets(dict(zip(self.key_names, key_tuple)))
        assert len(datasets) == 1
        path = datasets[key_tuple]

        if tile_size is None:
            tile_size = settings.DEFAULT_TILE_SIZE

        # make sure all arguments are hashable
        kwargs = dict(
            path=path,
            tile_bounds=tuple(tile_bounds) if tile_bounds else None,
            tile_size=tuple(tile_size),
            preserve_values=preserve_values,
            reprojection_method=settings.REPROJECTION_METHOD,
            resampling_method=settings.RESAMPLING_METHOD
        )

        cache_key = hash(tuple(kwargs.items()))

        try:
            with self._cache_lock:
                result = self._raster_cache[cache_key]
        except KeyError:
            pass
        else:
            if asynchronous:
                # wrap result in a future
                future = Future()
                future.set_result(result)
                return future
            else:
                return result

        retrieve_tile = functools.partial(self._get_raster_tile, **kwargs)

        future = submit_to_executor(retrieve_tile)

        def cache_callback(future: Future) -> None:
            # insert result into global cache if execution was successful
            if future.exception() is None:
                self._add_to_cache(cache_key, future.result())

        if asynchronous:
            future.add_done_callback(cache_callback)
            return future
        else:
            result = future.result()
            cache_callback(future)
            return result

    def _add_to_cache(self, key: Any, value: Any) -> None:
        try:
            with self._cache_lock:
                self._raster_cache[key] = value
        except ValueError:  # value too large
            pass
