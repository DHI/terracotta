"""api/metadata.py

Flask route to handle /metadata calls.
"""

from marshmallow import Schema, fields, validate
from flask import jsonify

from terracotta.api.flask_api import convert_exceptions, metadata_api, spec


class MetadataSchema(Schema):
    keys = fields.List(fields.String(), description='Keys identifying dataset')
    bounds = fields.List(fields.Number(), validate=validate.Length(equal=4),
                         description='Physical bounds of dataset in WGS84 projection')
    nodata = fields.Number(allow_none=True, description='Nodata value (if given)')
    range = fields.List(fields.Number(), validate=validate.Length(equal=2),
                        description='Minimum and maximum data value')
    mean = fields.Number(description='Data mean')
    stdev = fields.Number(description='Data standard deviation')
    percentiles = fields.List(fields.Number(), validate=validate.Length(equal=98),
                              description='1st, 2nd, 3rd, ..., 98th data percentile')
    metadata = fields.Raw(description='Any additional (manually added) metadata')


@metadata_api.route('/metadata/<path:keys>', methods=['GET'])
@convert_exceptions
def get_metadata(keys: str) -> str:
    """Get metadata for given dataset
    ---
    get:
        summary: /metadata
        description: Retrieve metadata for given dataset (identified by keys).
        parameters:
          - name: keys
            in: path
            description: Keys of dataset to retrieve metadata for (e.g. 'value1/value2')
            type: path
            required: true
        responses:
            200:
                description: All metadata for given dataset
                schema: MetadataSchema
            404:
                description: No dataset found for given key combination
    """
    from terracotta.handlers.metadata import metadata
    parsed_keys = [key for key in keys.split('/') if key]
    payload = metadata(parsed_keys)
    schema = MetadataSchema()
    print(payload)
    return jsonify(schema.dump(payload))


spec.definition('Metadata', schema=MetadataSchema)
