"""api/rgb.py

Flask route to handle /rgb calls.
"""

from typing import Any, Mapping, Dict
import json

from marshmallow import Schema, fields, validate, pre_load, ValidationError
from flask import request, send_file

from terracotta.api.flask_api import convert_exceptions, tile_api, spec


class RGBQuerySchema(Schema):
    keys = fields.String(required=True, description='Keys identifying dataset, in order')
    tile_z = fields.Int(required=True, description='Requested zoom level')
    tile_y = fields.Int(required=True, description='y coordinate')
    tile_x = fields.Int(required=True, description='x coordinate')


class RGBOptionSchema(Schema):
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

    @pre_load
    def process_ranges(self, data: Mapping[str, Any]) -> Dict[str, Any]:
        data = dict(data.items())
        for var in ('r_range', 'g_range', 'b_range'):
            val = data.get(var)
            if val:
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    raise ValidationError(f'Could not decode value for {var} as JSON') from exc
        print(data)
        return data


@tile_api.route('/rgb/<int:tile_z>/<int:tile_x>/<int:tile_y>.png')
@tile_api.route('/rgb/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@convert_exceptions
def get_rgb(tile_z: int, tile_y: int, tile_x: int, keys: str = '') -> Any:
    """Return the requested RGB tile as a PNG image.
    ---
    get:
        summary: /rgb
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
    from terracotta.handlers.rgb import rgb

    some_keys = [key for key in keys.split('/') if key]
    tile_xyz = (tile_x, tile_y, tile_z)

    option_schema = RGBOptionSchema()
    options = option_schema.load(request.args)

    rgb_values = (options['r'], options['g'], options['b'])
    stretch_ranges = tuple(options[k] for k in ('r_range', 'g_range', 'b_range'))

    image = rgb(
        some_keys, tile_xyz, rgb_values, stretch_ranges=stretch_ranges
    )

    return send_file(image, mimetype='image/png')


spec.definition('RGBOptions', schema=RGBOptionSchema)
