from typing import Sequence, List, Mapping, Any
from typing.io import BinaryIO

from terracotta.database import requires_database, Database
from terracotta import settings, tile, encode_decode


@requires_database
def keys(db: Database) -> List[str]:
    """List available keys, in order"""
    raise NotImplementedError


@requires_database
def datasets(db: Database, some_keys: Mapping[str, str] = None) -> List[Mapping[str, str]]:
    """List all available key combinations"""
    raise NotImplementedError


@requires_database
def metadata(db: Database, keys: Mapping[str, str]) -> Mapping[str, Any]:
    """Returns all metadata for a single dataset"""
    raise NotImplementedError


@requires_database
def rgb(db: Database, some_keys: Mapping[str, str], xyz: Sequence[int], rgb_values: Sequence[str],
        *, color_options: Mapping[str, Any] = None) -> BinaryIO:
    """Return RGB image

    Red, green, and blue channels correspond to the given values `rgb_values` of the key
    missing from `some_keys`.
    """
    import numpy as np

    color_options = color_options or {}
    color_stretch_method = color_options.get('method', 'stretch')

    if len(rgb_values) != 3:
        raise ValueError('rgb_values argument must contain three values')

    available_keys = db.get('keys')
    unspecified_key = set(some_keys.keys()) - set(available_keys)

    if len(unspecified_key) != 1:
        raise ValueError('some_keys argument must specify all keys except one')

    unspecified_key = unspecified_key[0]

    if len(xyz) != 3:
        raise ValueError('xyz argument must contain three values')

    tile_size = settings.TILE_SIZE
    out = np.empty(tile_size + (3,), dtype='uint8')

    for i, band_key in enumerate(rgb_values):
        band_keys = some_keys.copy()
        band_keys[unspecified_key] = band_key

        metadata = db.get('metadata', where=band_keys, only=['path', 'min', 'max'])
        assert len(metadata) == 1

        filepath = metadata[0]['path']

        try:
            tiledata = tile.get_tile(filepath, *xyz, tile_size=tile_size)
        except tile.TileOutOfBoundsError:
            out[...] = np.nan
            break

        if color_stretch_method == 'stretch':
            stretch_range = [color_options.get(k, metadata[k]) for k in ('min', 'max')]
        elif color_stretch_method == 'histogram_cut':
            stretch_percentile = color_options.get('percentiles', (2, 98))
            chist = db.get('metadata', where=band_keys, only=['cumulative_histogram'])['cumulative_histogram']
            stretch_range = encode_decode.percentile_from_cumulative_histogram(chist, stretch_percentile)
        else:
            raise ValueError(f'unrecognized stretching method {color_stretch_method}')

        out[..., i] = encode_decode.to_uint8(tiledata, *stretch_range)

    alpha_mask = np.any(np.isnan(out), axis=-1)
    return encode_decode.to_png(out, alpha_mask=alpha_mask)


@requires_database
def singleband(db: Database, keys: Mapping[str, str], xyz: Sequence[int], *,
               color_options: Mapping[str, str] = None) -> BinaryIO:
    """Return singleband image"""
    raise NotImplementedError


@requires_database
def colorbar(db: Database, keys: Mapping[str, str], xyz: Sequence[int], *,
             color_options: Mapping[str, str] = None) -> Mapping[int, str]:
    """Returns a mapping pixel value -> color hex for given image"""
    raise NotImplementedError


@requires_database
def legend(db: Database, keys: Mapping[str, str], xyz: Sequence[int]):
    """Returns mapping legend for categorical data"""
    raise NotImplementedError
