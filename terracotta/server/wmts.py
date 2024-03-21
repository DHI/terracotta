"""server/wmts.py

Flask route to handle /wmts calls.
"""

from flask import jsonify, Response, request
from marshmallow import Schema, fields, EXCLUDE

from terracotta.server.flask_api import METADATA_API


class DimensionOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    dimension = fields.String(required=False, default=None, description='Key to make dimension along')


@METADATA_API.route('/wmts', methods=['GET'])
def get_wmts_capabilities() -> Response:
    from terracotta.handlers.wmts import wmts
    option_schema = DimensionOptionSchema()
    options = option_schema.load(request.args)

    capabilities = wmts(request.url_root, options.get('dimension'))
    return Response(capabilities, mimetype='text/xml')
