"""api/colormaps.py

Flask route to handle /colormaps calls.
"""

from flask import jsonify
from marshmallow import Schema, fields

from terracotta.api.flask_api import convert_exceptions, metadata_api, spec


class ColormapSchema(Schema):
    colormaps = fields.List(fields.String(example='viridis'), required=True)


@metadata_api.route('/colormaps', methods=['GET'])
@convert_exceptions
def get_colormaps() -> str:
    """Get all registered colormaps.
    ---
    get:
        summary: /colormaps
        description:
            Get all registered colormaps. For a preview see
            https://matplotlib.org/examples/color/colormaps_reference.html
        responses:
            200:
                description: List of names of all colormaps
                schema: ColormapSchema
    """
    from terracotta.handlers.colormaps import colormaps
    payload = {'colormaps': colormaps()}
    schema = ColormapSchema()
    return jsonify(schema.dump(payload))


spec.definition('Colormaps', schema=ColormapSchema)
