"""raster.py

Extract information from raster files through rasterio.
"""

from typing import Optional, Any, Dict, Tuple, Sequence, TYPE_CHECKING
import contextlib
import warnings
import logging

import numpy as np

if TYPE_CHECKING:  # pragma: no cover
    from rasterio.io import DatasetReader  # noqa: F401

try:
    from crick import TDigest, SummaryStats
    has_crick = True
except ImportError:  # pragma: no cover
    has_crick = False

from terracotta import exceptions
from terracotta.profile import trace

logger = logging.getLogger(__name__)


def convex_hull_candidate_mask(mask: np.ndarray) -> np.ndarray:
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


def compute_image_stats_chunked(dataset: 'DatasetReader') -> Optional[Dict[str, Any]]:
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
            hull_candidates = convex_hull_candidate_mask(~block_data.mask)
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


def compute_image_stats(dataset: 'DatasetReader',
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
        hull_candidates = convex_hull_candidate_mask(~raster_data.mask)
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


@trace('compute_metadata')
def compute_metadata(path: str, *,
                     extra_metadata: Any = None,
                     use_chunks: bool = None,
                     max_shape: Sequence[int] = None,
                     large_raster_threshold: int = None,
                     rio_env_options: Dict[str, Any] = None) -> Dict[str, Any]:
    import rasterio
    from rasterio import warp
    from terracotta.cog import validate

    row_data: Dict[str, Any] = {}
    extra_metadata = extra_metadata or {}

    if max_shape is not None and len(max_shape) != 2:
        raise ValueError('max_shape argument must contain 2 values')

    if use_chunks and max_shape is not None:
        raise ValueError('Cannot use both use_chunks and max_shape arguments')

    if rio_env_options is None:
        rio_env_options = {}

    with rasterio.Env(**rio_env_options):
        if not validate(path):
            warnings.warn(
                f'Raster file {path} is not a valid cloud-optimized GeoTIFF. '
                'Any interaction with it will be significantly slower. Consider optimizing '
                'it through `terracotta optimize-rasters` before ingestion.',
                exceptions.PerformanceWarning, stacklevel=3
            )

        with rasterio.open(path) as src:
            if src.nodata is None and not has_alpha_band(src):
                warnings.warn(
                    f'Raster file {path} does not have a valid nodata value, '
                    'and does not contain an alpha band. No data will be masked.'
                )

            bounds = warp.transform_bounds(
                src.crs, 'epsg:4326', *src.bounds, densify_pts=21
            )

            if use_chunks is None and max_shape is None and large_raster_threshold is not None:
                use_chunks = src.width * src.height > large_raster_threshold

                if use_chunks:
                    logger.debug(
                        f'Computing metadata for file {path} using more than '
                        f'{large_raster_threshold // 10**6}M pixels, iterating '
                        'over chunks'
                    )

            if use_chunks and not has_crick:
                warnings.warn(
                    'Processing a large raster file, but crick failed to import. '
                    'Reading whole file into memory instead.', exceptions.PerformanceWarning
                )
                use_chunks = False

            if use_chunks:
                raster_stats = compute_image_stats_chunked(src)
            else:
                raster_stats = compute_image_stats(src, max_shape)

    if raster_stats is None:
        raise ValueError(f'Raster file {path} does not contain any valid data')

    row_data.update(raster_stats)

    row_data['bounds'] = bounds
    row_data['metadata'] = extra_metadata
    return row_data


def get_resampling_enum(method: str) -> Any:
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


def has_alpha_band(src: 'DatasetReader') -> bool:
    from rasterio.enums import MaskFlags, ColorInterp
    return (
        any([MaskFlags.alpha in flags for flags in src.mask_flag_enums])
        or ColorInterp.alpha in src.colorinterp
    )


@trace("get_raster_tile")
def get_raster_tile(path: str, *,
                    reprojection_method: str = "nearest",
                    resampling_method: str = "nearest",
                    tile_bounds: Tuple[float, float, float, float] = None,
                    tile_size: Tuple[int, int] = (256, 256),
                    preserve_values: bool = False,
                    target_crs: str = 'epsg:3857',
                    rio_env_options: Dict[str, Any] = None) -> np.ma.MaskedArray:
    """Load a raster dataset from a file through rasterio.

    Heavily inspired by mapbox/rio-tiler
    """
    import rasterio
    from rasterio import transform, windows, warp
    from rasterio.vrt import WarpedVRT
    from affine import Affine

    dst_bounds: Tuple[float, float, float, float]

    if rio_env_options is None:
        rio_env_options = {}

    if preserve_values:
        reproject_enum = resampling_enum = get_resampling_enum('nearest')
    else:
        reproject_enum = get_resampling_enum(reprojection_method)
        resampling_enum = get_resampling_enum(resampling_method)

    with contextlib.ExitStack() as es:
        es.enter_context(rasterio.Env(**rio_env_options))
        try:
            with trace('open_dataset'):
                src = es.enter_context(rasterio.open(path))
        except OSError:
            raise IOError('error while reading file {}'.format(path))

        # compute buonds in target CRS
        dst_bounds = warp.transform_bounds(src.crs, target_crs, *src.bounds)

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
            src.crs, target_crs, src.width, src.height, *src.bounds
        )
        dst_res = (abs(dst_transform.a), abs(dst_transform.e))

        # in some cases (e.g. at extreme latitudes), the default transform
        # suggests very coarse resolutions - in this case, fall back to native tile res
        tile_transform = transform.from_bounds(*tile_bounds, *tile_size)
        tile_res = (abs(tile_transform.a), abs(tile_transform.e))

        if tile_res[0] < dst_res[0] or tile_res[1] < dst_res[1]:
            dst_res = tile_res
            resampling_enum = get_resampling_enum('nearest')

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
                src, crs=target_crs, resampling=reproject_enum,
                transform=vrt_transform, width=vrt_width, height=vrt_height,
                add_alpha=not has_alpha_band(src)
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
