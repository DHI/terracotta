"""api/keys.py

Flask route to handle /keys calls.
"""

from flask import jsonify
from marshmallow import Schema, fields

from terracotta.api.flask_api import convert_exceptions, metadata_api, spec


class KeySchema(Schema):
    keys = fields.List(fields.String(), required=True, description='List of known keys')


@metadata_api.route('/keys', methods=['GET'])
@convert_exceptions
def get_keys() -> str:
    """Get all key names
    ---
    get:
        summary: /keys
        description: List the names of all known keys.
        responses:
            200:
                description: Array containing key names
                schema: KeySchema
    """
    from terracotta.handlers.keys import keys
    schema = KeySchema()
    payload = {'keys': keys()}
    return jsonify(schema.dump(payload))


spec.definition('Keys', schema=KeySchema)
