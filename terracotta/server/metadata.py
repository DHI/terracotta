"""server/metadata.py

Flask route to handle /metadata calls.
"""

from marshmallow import Schema, fields, validate, ValidationError
from flask import jsonify, Response, request

from terracotta.server.flask_api import METADATA_API


class MetadataSchema(Schema):
    class Meta:
        ordered = True

    keys = fields.Dict(
        keys=fields.String(),
        values=fields.String(),
        description="Keys identifying dataset",
        required=True,
    )
    bounds = fields.List(
        fields.Number(),
        validate=validate.Length(equal=4),
        required=True,
        description="Physical bounds of dataset in WGS84 projection",
    )
    convex_hull = fields.Dict(
        required=True, description="GeoJSON representation of the dataset's convex hull"
    )
    valid_percentage = fields.Number(
        description="Percentage of valid data in the dataset"
    )
    range = fields.List(
        fields.Number(),
        validate=validate.Length(equal=2),
        required=True,
        description="Minimum and maximum data value",
    )
    mean = fields.Number(description="Data mean", required=True)
    stdev = fields.Number(description="Data standard deviation", required=True)
    percentiles = fields.List(
        fields.Number(),
        validate=validate.Length(equal=99),
        required=True,
        description="1st, 2nd, 3rd, ..., 99th data percentile",
    )
    metadata = fields.Raw(
        description="Any additional (manually added) metadata", required=True
    )


class CommaSeparatedListField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            assert value[0] == "[" and value[-1] == "]"

            if value == "[]":
                return []

            return value[1:-1].split(', ')
        except ValueError:
            raise ValidationError("Invalid input for a list of values.")


class MetadataColumnsSchema(Schema):
    columns = CommaSeparatedListField(
        description="Columns of dataset to be returned"
    )


class MultipleMetadataDatasetsSchema(Schema):
    keys = fields.List(
        fields.List(
            fields.String(),
            description="Keys identifying dataset",
            required=True,
        ),
        required=True,
        description="Array containing all available key combinations",
    )


@METADATA_API.route("/metadata/<path:keys>", methods=["GET"])
def get_metadata(keys: str) -> Response:
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
          - in: query
            schema: MetadataColumnsSchema
        responses:
            200:
                description: All metadata for given dataset
                schema: MetadataSchema
            404:
                description: No dataset found for given key combination
    """
    from terracotta.handlers.metadata import metadata

    columns_schema = MetadataColumnsSchema()
    columns = columns_schema.load(request.args).get("columns")

    parsed_keys = [key for key in keys.split("/") if key]

    payload = metadata(columns, parsed_keys)
    schema = MetadataSchema(partial=columns is not None)
    return jsonify(schema.load(payload))


@METADATA_API.route("/metadata", methods=["POST"])
def get_multiple_metadata() -> Response:
    """Get metadata for multiple datasets
    ---
    post:
        summary: /metadata
        description:
            Retrieve metadata for multiple datasets, identified by the
            body payload. Desired columns can be filtered using the ?columns
            query.
        parameters:
          - in: query
            schema: MetadataColumnsSchema
          - in: body
            schema: MultipleMetadataDatasetsSchema
        responses:
            200:
                description: All metadata for given dataset
                schema: MetadataSchema
            404:
                description: No dataset found for given key combination
    """
    from terracotta.handlers.metadata import multiple_metadata

    datasets_schema = MultipleMetadataDatasetsSchema()
    datasets = datasets_schema.load(request.json).get("keys")

    columns_schema = MetadataColumnsSchema()
    columns = columns_schema.load(request.args).get("columns")

    schema = MetadataSchema(many=True, partial=columns is not None)
    return jsonify(schema.load(multiple_metadata(columns, datasets)))
