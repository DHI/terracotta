"""server/rgb.py

Flask route to handle /rgb calls.
"""

from typing import Any, Mapping, Dict, Tuple
import json

from marshmallow import Schema, fields, validate, pre_load, ValidationError, EXCLUDE
from flask import request, send_file, Response

from terracotta.server.flask_api import TILE_API


class RGBQuerySchema(Schema):
    keys = fields.String(required=True, description='Keys identifying dataset, in order')
    tile_z = fields.Int(required=True, description='Requested zoom level')
    tile_y = fields.Int(required=True, description='y coordinate')
    tile_x = fields.Int(required=True, description='x coordinate')


class RGBOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    r = fields.String(required=True, description='Key value for red band')
    g = fields.String(required=True, description='Key value for green band')
    b = fields.String(required=True, description='Key value for blue band')
    r_range = fields.List(
        fields.Number(allow_none=True), validate=validate.Length(equal=2), example='[0,1]',
        missing=None, description='Stretch range [min, max] to use for red band as JSON array'
    )
    g_range = fields.List(
        fields.Number(allow_none=True), validate=validate.Length(equal=2), example='[0,1]',
        missing=None, description='Stretch range [min, max] to use for green band as JSON array'
    )
    b_range = fields.List(
        fields.Number(allow_none=True), validate=validate.Length(equal=2), example='[0,1]',
        missing=None, description='Stretch range [min, max] to use for blue band as JSON array'
    )
    tile_size = fields.List(
        fields.Integer(), validate=validate.Length(equal=2), example='[256,256]',
        description='Pixel dimensions of the returned PNG image as JSON list.'
    )

    @pre_load
    def process_ranges(self, data: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        data = dict(data.items())
        for var in ('r_range', 'g_range', 'b_range', 'tile_size'):
            val = data.get(var)
            if val:
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    raise ValidationError(f'Could not decode value for {var} as JSON') from exc
        return data


@TILE_API.route('/rgb/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@TILE_API.route('/rgb/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
def get_rgb(tile_z: int, tile_y: int, tile_x: int, keys: str = '') -> Response:
    """Return the requested RGB tile as a PNG image.
    ---
    get:
        summary: /rgb (tile)
        description: Combine three datasets to RGB image, and return tile as PNG
        parameters:
            - in: path
              schema: RGBQuerySchema
            - in: query
              schema: RGBOptionSchema
        responses:
            200:
                description:
                    PNG image of requested tile
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    tile_xyz = (tile_x, tile_y, tile_z)
    return _get_rgb_image(keys, tile_xyz=tile_xyz)


class RGBPreviewQuerySchema(Schema):
    keys = fields.String(required=True, description='Keys identifying dataset, in order')


@TILE_API.route('/rgb/preview.png', methods=['GET'])
@TILE_API.route('/rgb/<path:keys>/preview.png', methods=['GET'])
def get_rgb_preview(keys: str = '') -> Response:
    """Return the requested RGB dataset preview as a PNG image.
    ---
    get:
        summary: /rgb (preview)
        description: Combine three datasets to RGB image, and return preview as PNG
        parameters:
            - in: path
              schema: RGBPreviewQuerySchema
            - in: query
              schema: RGBOptionSchema
        responses:
            200:
                description:
                    PNG image of requested tile
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    return _get_rgb_image(keys)


def _get_rgb_image(keys: str, tile_xyz: Tuple[int, int, int] = None) -> Response:
    from terracotta.handlers.rgb import rgb

    option_schema = RGBOptionSchema()
    options = option_schema.load(request.args)

    some_keys = [key for key in keys.split('/') if key]

    rgb_values = (options.pop('r'), options.pop('g'), options.pop('b'))
    stretch_ranges = tuple(options.pop(k) for k in ('r_range', 'g_range', 'b_range'))

    image = rgb(
        some_keys, rgb_values, stretch_ranges=stretch_ranges, tile_xyz=tile_xyz, **options
    )

    return send_file(image, mimetype='image/png')
