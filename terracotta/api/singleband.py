"""api/singleband.py

Flask route to handle /singleband calls.
"""

from typing import Any, Mapping, Dict
import json

from marshmallow import (Schema, fields, validate, validates_schema,
                         pre_load, ValidationError, EXCLUDE)
from flask import request, send_file

from terracotta.api.flask_api import convert_exceptions, tile_api
from terracotta.cmaps import AVAILABLE_CMAPS


class SinglebandQuerySchema(Schema):
    keys = fields.String(required=True, description='Keys identifying dataset, in order')
    tile_z = fields.Int(required=True, description='Requested zoom level')
    tile_y = fields.Int(required=True, description='y coordinate')
    tile_x = fields.Int(required=True, description='x coordinate')


class SinglebandOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    stretch_range = fields.List(
        fields.Number(allow_none=True), validate=validate.Length(equal=2), example='[0,1]',
        description='Stretch range to use as JSON array, uses full range by default. '
                    'Null values indicate global minimum / maximum.', missing=None
    )

    colormap = fields.String(
        description='Colormap to apply to image (see /colormap)',
        validate=validate.OneOf(('explicit', *AVAILABLE_CMAPS)), missing=None
    )

    explicit_color_map = fields.Dict(
        keys=fields.Number(),
        values=fields.List(fields.Number, validate=validate.Length(equal=3)),
        example='{{0: (255, 255, 255)}}',
        description='Explicit value-color mapping to use as JSON object. '
                    'Must be given together with colormap=explicit. Color values can be '
                    'specified either as RGB tuple (in the range of [0, 255]), or as '
                    'hex strings.'
    )

    @validates_schema
    def validate_cmap(self, data: Mapping[str, Any]) -> None:
        if data.get('colormap', '') == 'explicit' and not data.get('explicit_color_map'):
            raise ValidationError('explicit_color_map argument must be given for colormap=explicit',
                                  'colormap')

        if data.get('explicit_color_map') and data.get('colormap', '') != 'explicit':
            raise ValidationError('explicit_color_map can only be given for colormap=explicit',
                                  'explicit_color_map')

    @pre_load
    def decode_json(self, data: Mapping[str, Any]) -> Dict[str, Any]:
        data = dict(data.items())
        for var in ('stretch_range', 'explicit_color_map'):
            val = data.get(var)
            if val:
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    raise ValidationError(f'Could not decode value for {var} as JSON') from exc

        val = data.get('explicit_color_map')
        if val and isinstance(val, dict):
            for key, color in val.items():
                if isinstance(color, str):
                    hex_string = color.lstrip('#')
                    try:
                        rgb = [int(hex_string[i:i + 2], 16) for i in (0, 2, 4)]
                        data['explicit_color_map'][key] = rgb
                    except ValueError:
                        msg = f'Could not decode value {color} in explicit_color_map as hex string'
                        raise ValidationError(msg)

        return data


@tile_api.route('/singleband/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
@convert_exceptions
def get_singleband(tile_z: int, tile_y: int, tile_x: int, keys: str) -> Any:
    """Return PNG image of requested singleband tile
    ---
    get:
        summary: /singleband
        description: Return PNG image of requested tile
        parameters:
            - in: path
              schema: SinglebandQuerySchema
            - in: query
              schema: SinglebandOptionSchema
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
    from terracotta.handlers.singleband import singleband

    parsed_keys = [key for key in keys.split('/') if key]

    tile_xyz = (tile_x, tile_y, tile_z)

    option_schema = SinglebandOptionSchema()
    options = option_schema.load(request.args)

    if options.get('colormap', '') == 'explicit':
        options['colormap'] = options.pop('explicit_color_map')

    image = singleband(parsed_keys, tile_xyz, **options)

    return send_file(image, mimetype='image/png')
