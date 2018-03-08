from io import BytesIO

from flask import Blueprint, current_app, abort, send_file
import numpy as np

import terracotta
from terracotta.tile import TileNotFoundError, TileOutOfBoundsError


tile_api = Blueprint('tile_api', __name__)
tilestore = None


def init_tilestore(datasets, options):
    global tilestore
    tilestore = terracotta.tile.TileStore(datasets, options['max_cache_size'])


@tile_api.route('/terracotta/<dataset>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@tile_api.route('/terracotta/<dataset>/<timestep>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
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
