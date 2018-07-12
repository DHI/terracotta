"""api/datasets.py

Flask route to handle /datasets calls.
"""

from flask import request, jsonify
from marshmallow import Schema, fields

from terracotta.api.flask_api import convert_exceptions, metadata_api, spec


class WhereSchema(Schema):
    key1 = fields.String(example='value1', description='Value of key1')
    key2 = fields.String(example='value2', description='Value of key2')


class DatasetSchema(Schema):
    datasets = fields.List(fields.Dict(values=fields.String(example='value1'),
                                       keys=fields.String(example='key1')),
                           required=True,
                           description='Array containing all available key combinations')


@metadata_api.route('/datasets', methods=['GET'])
@convert_exceptions
def get_datasets() -> str:
    """Get all available key combinations
    ---
    get:
        summary: /datasets
        description:
            Get keys of all available datasets that match given key constraint.
            Constraints may be combined freely. Returns all known datasets if not query parameters
            are given.
        parameters:
          - in: query
            schema: WhereSchema
        responses:
            200:
                description: All available key combinations
                schema:
                    type: array
                    items: DatasetSchema
            400:
                description: Query parameters contain unrecognized keys
    """
    from terracotta.handlers.datasets import datasets
    keys = dict(request.args.items()) or None
    payload = {'datasets': datasets(keys)}
    schema = DatasetSchema()
    return jsonify(schema.dump(payload))


spec.definition('Dataset', schema=DatasetSchema)
