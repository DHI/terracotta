from io import BytesIO

from flask import Blueprint, current_app, abort, send_file
import numpy as np
from cachetools import LFUCache, cached

import terracotta.tile as tile
from terracotta.tile import TileNotFoundError, TileOutOfBoundsError


DEFAULT_CACHE_SIZE = 1000000000  # 1GB


tile_api = Blueprint('tile_api', __name__)
cache = None
tilestore = None


def init(datasets, cache_size=DEFAULT_CACHE_SIZE):
    global cache
    global tilestore
    cache = LFUCache(cache_size)
    tilestore = tile.TileStore(datasets)


@tile_api.route('/<dataset>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@tile_api.route('/<dataset>/<timestep>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
@cached(cache)
def get_tile(dataset, tile_z, tile_x, tile_y, timestep=None):
    """Respond to tile requests"""

    try:
        img = tilestore.tile(tile_x, tile_y, tile_z, dataset, timestep, contrast_stretch=True)
    except TileNotFoundError:
        if current_app.debug:
            raise
        abort(404)
    except TileOutOfBoundsError:
        nodata = tilestore.get_nodata(dataset)
        img = np.full((256, 256), nodata, dtype=np.uint8)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=0)
    sio.seek(0)

    return send_file(sio, mimetype='image/png')
