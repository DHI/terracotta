"""api/singleband.py

Flask route to handle /singleband calls.
"""

from typing import Any, Mapping, Dict
import json

from marshmallow import Schema, fields, validate, pre_load, ValidationError, EXCLUDE
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
    colormap = fields.String(description='Colormap to apply to image (see /colormap)',
                             missing=None, validate=validate.OneOf(AVAILABLE_CMAPS))

    @pre_load
    def process_ranges(self, data: Mapping[str, Any]) -> Dict[str, Any]:
        data = dict(data.items())
        var = 'stretch_range'
        val = data.get(var)
        if val:
            try:
                data[var] = json.loads(val)
            except json.decoder.JSONDecodeError as exc:
                raise ValidationError(f'Could not decode value for {var} as JSON') from exc
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

    image = singleband(
        parsed_keys, tile_xyz, **options
    )

    return send_file(image, mimetype='image/png')
