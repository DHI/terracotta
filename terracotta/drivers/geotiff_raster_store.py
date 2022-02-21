"""drivers/geotiff_raster_store.py

Base class for drivers operating on physical raster files.
"""

from typing import Any, Callable, Sequence, Dict, TypeVar
from concurrent.futures import Future, Executor, ProcessPoolExecutor, ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool

import functools
import logging
import warnings
import threading

import numpy as np

from terracotta import get_settings
from terracotta import raster
from terracotta.cache import CompressedLFUCache
from terracotta.drivers.base_classes import RasterStore

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


def ensure_hashable(val: Any) -> Any:
    if isinstance(val, list):
        return tuple(val)

    if isinstance(val, dict):
        return tuple((k, ensure_hashable(v)) for k, v in val.items())

    return val


class GeoTiffRasterStore(RasterStore):
    """Raster store that operates on GeoTiff raster files from disk.

    Path arguments are expected to be file paths.
    """
    _TARGET_CRS: str = 'epsg:3857'
    _LARGE_RASTER_THRESHOLD: int = 10980 * 10980
    _RIO_ENV_OPTIONS = dict(
        GDAL_TIFF_INTERNAL_MASK=True,
        GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'
    )

    def __init__(self) -> None:
        settings = get_settings()
        self._raster_cache = CompressedLFUCache(
            settings.RASTER_CACHE_SIZE,
            compression_level=settings.RASTER_CACHE_COMPRESS_LEVEL
        )
        self._cache_lock = threading.RLock()

    def compute_metadata(self, path: str, *,
                         extra_metadata: Any = None,
                         use_chunks: bool = None,
                         max_shape: Sequence[int] = None) -> Dict[str, Any]:
        return raster.compute_metadata(path, extra_metadata=extra_metadata,
                                       use_chunks=use_chunks, max_shape=max_shape,
                                       large_raster_threshold=self._LARGE_RASTER_THRESHOLD,
                                       rio_env_options=self._RIO_ENV_OPTIONS)

    # return type has to be Any until mypy supports conditional return types
    def get_raster_tile(self,
                        path: str, *,
                        tile_bounds: Sequence[float] = None,
                        tile_size: Sequence[int] = None,
                        preserve_values: bool = False,
                        asynchronous: bool = False) -> Any:
        future: Future[np.ma.MaskedArray]
        result: np.ma.MaskedArray

        settings = get_settings()

        if tile_size is None:
            tile_size = settings.DEFAULT_TILE_SIZE

        kwargs = dict(
            path=path,
            tile_bounds=tile_bounds,
            tile_size=tuple(tile_size),
            preserve_values=preserve_values,
            reprojection_method=settings.REPROJECTION_METHOD,
            resampling_method=settings.RESAMPLING_METHOD,
            target_crs=self._TARGET_CRS,
            rio_env_options=self._RIO_ENV_OPTIONS,
        )

        cache_key = hash(ensure_hashable(kwargs))

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

        retrieve_tile = functools.partial(raster.get_raster_tile, **kwargs)

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
