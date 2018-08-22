"""api/keys.py

Flask route to handle /legend calls.
"""

from typing import Any, Mapping, Dict
import json

from flask import jsonify, request
from marshmallow import Schema, fields, validate, pre_load, ValidationError, EXCLUDE

from terracotta.api.flask_api import convert_exceptions, metadata_api, spec
from terracotta.cmaps import AVAILABLE_CMAPS


class LegendEntrySchema(Schema):
    value = fields.Number(required=True)
    rgb = fields.List(fields.Number(), required=True, validate=validate.Length(equal=3))


class LegendSchema(Schema):
    legend = fields.Nested(LegendEntrySchema, many=True, required=True)


class LegendOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    stretch_range = fields.List(
        fields.Number(), validate=validate.Length(equal=2), required=True,
        description='Minimum and maximum value of colormap as JSON array '
                    '(same as for /singleband and /rgb)'
    )
    colormap = fields.String(description='Name of color map to use (see /colormap)',
                             missing=None, validate=validate.OneOf(AVAILABLE_CMAPS))
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


@metadata_api.route('/legend', methods=['GET'])
@convert_exceptions
def get_legend() -> str:
    """Get a legend mapping pixel values to colors
    ---
    get:
        summary: /legend
        description:
            Get a legend mapping pixel values to colors. Use this to construct a color bar for a
            dataset.
        parameters:
            - in: query
              schema: LegendOptionSchema
        responses:
            200:
                description: Array containing data values and RGBA tuples
                schema: LegendSchema
            400:
                description: Query parameters are invalid
    """
    from terracotta.handlers.legend import legend

    input_schema = LegendOptionSchema()
    options = input_schema.load(request.args)

    payload = {'legend': legend(**options)}

    schema = LegendSchema()
    return jsonify(schema.load(payload))


spec.definition('LegendEntry', schema=LegendEntrySchema)
spec.definition('Legend', schema=LegendSchema)
