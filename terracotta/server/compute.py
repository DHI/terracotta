"""server/compute.py

Flask route to handle /compute calls.
"""

from typing import Any, Mapping, Dict, Tuple
import json

from marshmallow import (Schema, fields, validate,
                         pre_load, ValidationError, EXCLUDE)
from flask import request, send_file, Response

from terracotta.server.flask_api import TILE_API
from terracotta.cmaps import AVAILABLE_CMAPS


class ComputeQuerySchema(Schema):
    keys = fields.String(required=True, description='Keys identifying dataset, in order')
    tile_z = fields.Int(required=True, description='Requested zoom level')
    tile_y = fields.Int(required=True, description='y coordinate')
    tile_x = fields.Int(required=True, description='x coordinate')


def _operator_field(i: int) -> fields.String:
    return fields.String(
        description=f'Last key of variable v{i} in given expression.'
    )


class ComputeOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    expression = fields.String(
        description='Mathematical expression to execute.', example='(v1 - v2) / (v1 + v2)',
        required=True
    )

    stretch_range = fields.List(
        fields.Number(allow_none=True), validate=validate.Length(equal=2), example='[0,1]',
        description='Stretch range to use as JSON array.', required=True
    )

    colormap = fields.String(
        description='Colormap to apply to image (see /colormap).',
        validate=validate.OneOf(('explicit', *AVAILABLE_CMAPS)), missing=None
    )

    tile_size = fields.List(
        fields.Integer(), validate=validate.Length(equal=2), example='[256,256]',
        description='Pixel dimensions of the returned PNG image as JSON list.'
    )

    v1 = _operator_field(1)
    v2 = _operator_field(2)
    v3 = _operator_field(3)
    v4 = _operator_field(4)
    v5 = _operator_field(5)

    @pre_load
    def decode_json(self, data: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        data = dict(data.items())
        for var in ('stretch_range', 'tile_size'):
            val = data.get(var)
            if val:
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    msg = f'Could not decode value {val} for {var} as JSON'
                    raise ValidationError(msg) from exc

        return data


@TILE_API.route('/compute/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@TILE_API.route('/compute/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
def get_compute(tile_z: int, tile_y: int, tile_x: int, keys: str = '') -> Response:
    """Combine datasets into a single-band PNG image through a given mathematical expression
    ---
    get:
        summary: /compute (tile)
        description:
            Combine datasets into a single-band PNG image through a given mathematical expression
        parameters:
            - in: path
              schema: ComputeQuerySchema
            - in: query
              schema: ComputeOptionSchema
        responses:
            200:
                description:
                    PNG image of requested data
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    tile_xyz = (tile_x, tile_y, tile_z)
    return _get_compute_image(keys, tile_xyz)


class ComputePreviewSchema(Schema):
    keys = fields.String(required=True, description='Keys identifying dataset, in order')


@TILE_API.route('/compute/preview.png', methods=['GET'])
@TILE_API.route('/compute/<path:keys>/preview.png', methods=['GET'])
def get_compute_preview(keys: str = '') -> Response:
    """Combine datasets into a single-band PNG image through a given mathematical expression
    ---
    get:
        summary: /compute (preview)
        description:
            Combine datasets into a single-band PNG image through a given mathematical expression
        parameters:
            - in: path
              schema: ComputePreviewSchema
            - in: query
              schema: ComputeOptionSchema
        responses:
            200:
                description:
                    PNG image of requested data
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    return _get_compute_image(keys)


def _get_compute_image(keys: str, tile_xyz: Tuple[int, int, int] = None) -> Any:
    from terracotta.handlers.compute import compute

    parsed_keys = [key for key in keys.split('/') if key]

    option_schema = ComputeOptionSchema()
    options = option_schema.load(request.args)

    operand_keys = {}
    for i in range(1, 6):
        field_name = f'v{i}'
        if field_name not in options:
            continue

        operand_keys[field_name] = options.pop(field_name)

    expression = options.pop('expression')

    image = compute(expression, parsed_keys, operand_keys, tile_xyz=tile_xyz, **options)

    return send_file(image, mimetype='image/png')
