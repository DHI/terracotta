"""server/keys.py

Flask route to handle /keys calls.
"""

from flask import jsonify, Response
from marshmallow import Schema, fields

from terracotta.server.flask_api import METADATA_API


class KeyItemSchema(Schema):
    class Meta:
        ordered = True

    key = fields.String(description='Key name', required=True)
    description = fields.String(description='Key description')


class KeySchema(Schema):
    keys = fields.Nested(KeyItemSchema, many=True, required=True)


@METADATA_API.route('/keys', methods=['GET'])
def get_keys() -> Response:
    """Get all key names
    ---
    get:
        summary: /keys
        description: List the names and descriptions (if available) of all known keys.
        responses:
            200:
                description: Array containing keys
                schema: KeySchema
    """
    from terracotta.handlers.keys import keys
    schema = KeySchema()
    payload = {'keys': keys()}
    return jsonify(schema.load(payload))
