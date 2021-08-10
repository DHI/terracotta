"""server/datasets.py

Flask route to handle /datasets calls.
"""

from typing import Any, Dict, List, Union
from flask import request, jsonify, Response
from marshmallow import Schema, fields, validate, INCLUDE, post_load
import re

from terracotta.server.flask_api import METADATA_API


class DatasetOptionSchema(Schema):
    class Meta:
        unknown = INCLUDE

    # placeholder values to document keys
    key1 = fields.String(example='value1', description='Value of key1', dump_only=True)
    key2 = fields.String(example='value2', description='Value of key2', dump_only=True)

    # real options
    limit = fields.Integer(
        description='Maximum number of returned datasets per page', missing=100,
        validate=validate.Range(min=0)
    )
    page = fields.Integer(
        missing=0, description='Current dataset page', validate=validate.Range(min=0)
    )

    @post_load
    def list_items(self, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Union[str, List[str]]]:
        # Create lists of values supplied as stringified lists
        for key, value in data.items():
            if isinstance(value, str) and re.match(r'^\[.*\]$', value):
                data[key] = value[1:-1].split(',')
        return data


class DatasetSchema(Schema):
    class Meta:
        ordered = True

    page = fields.Integer(description='Current page', required=True)
    limit = fields.Integer(description='Maximum number of returned items', required=True)
    datasets = fields.List(
        fields.Dict(values=fields.String(example='value1'),
                    keys=fields.String(example='key1')),
        required=True,
        description='Array containing all available key combinations'
    )


@METADATA_API.route('/datasets', methods=['GET'])
def get_datasets() -> Response:
    """Get all available key combinations
    ---
    get:
        summary: /datasets
        description:
            Get keys of all available datasets that match given key constraint.
            Constraints may be combined freely. Returns all known datasets if no query parameters
            are given.
        parameters:
          - in: query
            schema: DatasetOptionSchema
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
    option_schema = DatasetOptionSchema()
    options = option_schema.load(request.args)

    limit = options.pop('limit')
    page = options.pop('page')
    keys = options or None

    payload = {
        'limit': limit,
        'page': page,
        'datasets': datasets(keys, page=page, limit=limit)
    }

    schema = DatasetSchema()
    return jsonify(schema.load(payload))
