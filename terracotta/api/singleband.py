from typing import Any
import json

from flask import request, send_file

from terracotta.api.flask_api import convert_exceptions, tile_api


@tile_api.route('/singleband/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
@convert_exceptions
def get_singleband(tile_z: int, tile_y: int, tile_x: int, path: str) -> Any:
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.singleband import singleband

    keys = [key for key in path.split('/') if key]

    tile_xyz = (tile_x, tile_y, tile_z)

    stretch_range = json.loads(request.args.get('stretch_range', 'null'))
    colormap = request.args.get('colormap')

    image = singleband(
        keys, tile_xyz, colormap=colormap, stretch_range=stretch_range
    )

    return send_file(image, mimetype='image/png')
