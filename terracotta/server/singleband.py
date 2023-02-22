"""server/singleband.py

Flask route to handle /singleband calls.
"""

from typing import Any, Mapping, Dict, Tuple
import json

from marshmallow import (Schema, fields, validate, validates_schema,
                         pre_load, ValidationError, EXCLUDE)
from flask import request, send_file, Response

from terracotta.server.flask_api import TILE_API
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
        values=fields.List(fields.Number, validate=validate.Length(min=3, max=4)),
        example='{0: (255, 255, 255)}',
        description='Explicit value-color mapping to use, encoded as JSON object. '
                    'Must be given together with `colormap=explicit`. Color values can be '
                    'specified either as RGB or RGBA tuple (in the range of [0, 255]), or as '
                    'hex strings.'
    )

    tile_size = fields.List(
        fields.Integer(), validate=validate.Length(equal=2), example='[256,256]',
        description='Pixel dimensions of the returned PNG image as JSON list.'
    )

    @validates_schema
    def validate_cmap(self, data: Mapping[str, Any], **kwargs: Any) -> None:
        if data.get('colormap', '') == 'explicit' and not data.get('explicit_color_map'):
            raise ValidationError('explicit_color_map argument must be given for colormap=explicit',
                                  'colormap')

        if data.get('explicit_color_map') and data.get('colormap', '') != 'explicit':
            raise ValidationError('explicit_color_map can only be given for colormap=explicit',
                                  'explicit_color_map')

    @pre_load
    def decode_json(self, data: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        data = dict(data.items())
        for var in ('stretch_range', 'tile_size', 'explicit_color_map'):
            val = data.get(var)
            if val:
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    msg = f'Could not decode value {val} for {var} as JSON'
                    raise ValidationError(msg) from exc

        val = data.get('explicit_color_map')
        if val and isinstance(val, dict):
            for key, color in val.items():
                if isinstance(color, str):
                    # convert hex strings to RGBA
                    hex_string = color.lstrip('#')
                    try:
                        rgb = [int(hex_string[i:i + 2], 16) for i in (0, 2, 4)]
                        data['explicit_color_map'][key] = (*rgb, 255)
                    except ValueError:
                        msg = f'Could not decode value {color} in explicit_color_map as hex string'
                        raise ValidationError(msg)
                elif len(color) == 3:
                    # convert RGB to RGBA
                    data['explicit_color_map'][key] = (*color, 255)

        return data


@TILE_API.route('/singleband/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
def get_singleband(tile_z: int, tile_y: int, tile_x: int, keys: str) -> Response:
    """Return single-band PNG image of requested tile
    ---
    get:
        summary: /singleband (tile)
        description: Return single-band PNG image of requested XYZ tile
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
    tile_xyz = (tile_x, tile_y, tile_z)
    return _get_singleband_image(keys, tile_xyz)


class SinglebandPreviewSchema(Schema):
    keys = fields.String(required=True, description='Keys identifying dataset, in order')


@TILE_API.route('/singleband/<path:keys>/preview.png', methods=['GET'])
def get_singleband_preview(keys: str) -> Response:
    """Return single-band PNG preview image of requested dataset
    ---
    get:
        summary: /singleband (preview)
        description: Return single-band PNG preview image of requested dataset
        parameters:
            - in: path
              schema: SinglebandPreviewSchema
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
    return _get_singleband_image(keys)


def _get_singleband_image(keys: str, tile_xyz: Tuple[int, int, int] = None) -> Response:
    from terracotta.handlers.singleband import singleband

    parsed_keys = [key for key in keys.split('/') if key]

    option_schema = SinglebandOptionSchema()
    options = option_schema.load(request.args)

    if options.get('colormap', '') == 'explicit':
        options['colormap'] = options.pop('explicit_color_map')

    image = singleband(parsed_keys, tile_xyz=tile_xyz, **options)

    return send_file(image, mimetype='image/png')
