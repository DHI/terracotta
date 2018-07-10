from typing import Any
import json

from flask import request, send_file

from terracotta import exceptions
from terracotta.api.flask_api import convert_exceptions, tile_api


@tile_api.route('/rgb/<int:tile_z>/<int:tile_x>/<int:tile_y>.png')
@tile_api.route('/rgb/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@convert_exceptions
def get_rgb(tile_z: int, tile_y: int, tile_x: int, path: str = '') -> Any:
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.rgb import rgb

    some_keys = [key for key in path.split('/') if key]

    tile_xyz = (tile_x, tile_y, tile_z)
    rgb_values = [request.args.get(k) for k in ('r', 'g', 'b')]

    if not all(rgb_values):
        raise exceptions.InvalidArgumentsError('r, g, and b arguments must be given')

    stretch_ranges = [json.loads(request.args.get(f'{k}_range', 'null')) for k in ('r', 'g', 'b')]

    image = rgb(
        some_keys, tile_xyz, rgb_values, stretch_ranges=stretch_ranges
    )

    return send_file(image, mimetype='image/png')
