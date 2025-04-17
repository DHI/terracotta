"""server/metadata.py

Flask route to handle /metadata calls.
"""

from typing import Any, Mapping, Dict
import json

from marshmallow import Schema, fields, validate, pre_load, ValidationError
from flask import jsonify, Response, request

from terracotta.server.flask_api import METADATA_API
from terracotta.exceptions import InvalidArgumentsError


class MetadataSchema(Schema):
    keys = fields.Dict(
        keys=fields.String(),
        values=fields.String(),
        metadata={"description": "Keys identifying dataset"},
        required=True,
    )
    bounds = fields.List(
        fields.Float(),
        validate=validate.Length(equal=4),
        required=True,
        metadata={"description": "Physical bounds of dataset in WGS84 projection"},
    )
    convex_hull = fields.Dict(
        required=True,
        metadata={"description": "GeoJSON representation of the dataset's convex hull"},
    )
    valid_percentage = fields.Float(
        metadata={"description": "Percentage of valid data in the dataset"}
    )
    range = fields.List(
        fields.Float(),
        validate=validate.Length(equal=2),
        required=True,
        metadata={"description": "Minimum and maximum data value"},
    )
    mean = fields.Float(metadata={"description": "Data mean"}, required=True)
    stdev = fields.Float(
        metadata={"description": "Data standard deviation"}, required=True
    )
    percentiles = fields.List(
        fields.Float(),
        validate=validate.Length(equal=99),
        required=True,
        metadata={"description": "1st, 2nd, 3rd, ..., 99th data percentile"},
    )
    metadata = fields.Raw(
        metadata={"description": "Any additional (manually added) metadata"},
        required=True,
    )


class MetadataColumnsSchema(Schema):
    columns = fields.List(
        fields.String(),
        metadata={"description": "List of columns to return"},
        required=False,
    )

    @pre_load
    def validate_columns(
        self, data: Mapping[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        data = dict(data.items())
        var = "columns"
        val = data.get(var)
        if val:
            try:
                data[var] = json.loads(val)
            except json.decoder.JSONDecodeError as exc:
                raise ValidationError(
                    f"Could not decode value for {var} as JSON"
                ) from exc
        return data


class MultipleMetadataDatasetsSchema(Schema):
    keys = fields.List(
        fields.List(
            fields.String(),
            metadata={"description": "Keys identifying dataset"},
            required=True,
        ),
        required=True,
        metadata={"description": "Array containing all available key combinations"},
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
            400:
                description:
                    If the maximum number of requested datasets is exceeded
            404:
                description: No dataset found for given key combination
    """
    from terracotta.handlers.metadata import multiple_metadata

    request_body = request.json
    if not isinstance(request_body, dict):
        raise InvalidArgumentsError("Request body must be a JSON object")

    datasets_schema = MultipleMetadataDatasetsSchema()
    datasets = datasets_schema.load(request_body).get("keys")

    columns_schema = MetadataColumnsSchema()
    columns = columns_schema.load(request.args).get("columns")

    payload = multiple_metadata(columns, datasets)
    schema = MetadataSchema(many=True, partial=columns is not None)
    return jsonify(schema.load(payload))
