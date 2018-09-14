"""api/keys.py

Flask route to handle /colormap calls.
"""

from typing import Any, Mapping, Dict
import json

from flask import jsonify, request
from marshmallow import Schema, fields, validate, pre_load, ValidationError, EXCLUDE

from terracotta.api.flask_api import convert_exceptions, metadata_api, spec
from terracotta.cmaps import AVAILABLE_CMAPS


class colormapEntrySchema(Schema):
    value = fields.Number(required=True)
    rgb = fields.List(fields.Number(), required=True, validate=validate.Length(equal=3))


class colormapSchema(Schema):
    colormap = fields.Nested(colormapEntrySchema, many=True, required=True)


class colormapOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    stretch_range = fields.List(
        fields.Number(), validate=validate.Length(equal=2), required=True,
        description='Minimum and maximum value of colormap as JSON array '
                    '(same as for /singleband and /rgb)'
    )
    colormap = fields.String(
        description='Name of color map to use (for a preview see '
                    'https://matplotlib.org/examples/color/colormaps_reference.html)',
        missing=None, validate=validate.OneOf(AVAILABLE_CMAPS)
    )
    num_values = fields.Int(description='Number of values to return', missing=255)

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


@metadata_api.route('/colormap', methods=['GET'])
@convert_exceptions
def get_colormap() -> str:
    """Get a colormap mapping pixel values to colors
    ---
    get:
        summary: /colormap
        description:
            Get a colormap mapping pixel values to colors. Use this to construct a color bar for a
            dataset.
        parameters:
            - in: query
              schema: colormapOptionSchema
        responses:
            200:
                description: Array containing data values and RGBA tuples
                schema: colormapSchema
            400:
                description: Query parameters are invalid
    """
    from terracotta.handlers.colormap import colormap

    input_schema = colormapOptionSchema()
    options = input_schema.load(request.args)

    payload = {'colormap': colormap(**options)}

    schema = colormapSchema()
    return jsonify(schema.load(payload))


spec.definition('colormapEntry', schema=colormapEntrySchema)
spec.definition('colormap', schema=colormapSchema)
