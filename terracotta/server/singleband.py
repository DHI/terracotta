"""server/singleband.py

Flask route to handle /singleband calls.
"""

from typing import Optional, Any, Mapping, Dict, Tuple
from functools import partial
import json

from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    pre_load,
    ValidationError,
    EXCLUDE,
)
from flask import request, send_file, Response

from terracotta.server.fields import (
    StringOrNumber,
    validate_stretch_range,
    validate_color_transform,
)
from terracotta.server.flask_api import TILE_API
from terracotta.cmaps import AVAILABLE_CMAPS


class SinglebandQuerySchema(Schema):
    keys = fields.String(
        required=True, metadata={"description": "Keys identifying dataset, in order"}
    )
    tile_z = fields.Int(required=True, metadata={"description": "Requested zoom level"})
    tile_y = fields.Int(required=True, metadata={"description": "y coordinate"})
    tile_x = fields.Int(required=True, metadata={"description": "x coordinate"})


class SinglebandOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    stretch_range = fields.List(
        StringOrNumber(allow_none=True, validate=validate_stretch_range),
        validate=validate.Length(equal=2),
        metadata={
            "example": "[0,1]",
            "description": (
                "Stretch range [min, max] to use as JSON array. "
                "Min and max may be numbers to use as absolute range, or strings "
                "of the format `p<digits>` with an integer between 0 and 100 "
                "to use percentiles of the image instead. "
                "Null values indicate global minimum / maximum."
            ),
        },
        load_default=None,
    )

    colormap = fields.String(
        metadata={"description": "Colormap to apply to image (see /colormap)"},
        validate=validate.OneOf(("explicit", *AVAILABLE_CMAPS)),
        load_default=None,
    )

    explicit_color_map = fields.Dict(
        # TODO: that might be wrong?
        keys=fields.Float(),
        values=fields.List(fields.Float, validate=validate.Length(min=3, max=4)),
        metadata={
            "example": '{"0": [255, 255, 255]}',
            "description": (
                "Explicit value-color mapping to use, encoded as JSON object. "
                "Must be given together with `colormap=explicit`. Color values can be "
                "specified either as RGB or RGBA tuple (in the range of [0, 255]), or as "
                "hex strings."
            ),
        },
    )

    color_transform = fields.String(
        validate=partial(validate_color_transform, test_array_bands=1),
        load_default=None,
        metadata={
            "example": "gamma 1 1.5, sigmoidal 1 15 0.5",
            "description": (
                "Color transform DSL string from color-operations."
                "All color operations for singleband should specify band 1."
            ),
        },
    )

    tile_size = fields.List(
        fields.Integer(),
        validate=validate.Length(equal=2),
        metadata={
            "example": "[256,256]",
            "description": "Pixel dimensions of the returned PNG image as JSON list.",
        },
    )

    @validates_schema
    def validate_cmap(self, data: Mapping[str, Any], **kwargs: Any) -> None:
        if data.get("colormap", "") == "explicit" and not data.get(
            "explicit_color_map"
        ):
            raise ValidationError(
                "explicit_color_map argument must be given for colormap=explicit",
                "colormap",
            )

        if data.get("explicit_color_map") and data.get("colormap", "") != "explicit":
            raise ValidationError(
                "explicit_color_map can only be given for colormap=explicit",
                "explicit_color_map",
            )

    @pre_load
    def decode_json(self, data: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        data = dict(data.items())
        for var in ("stretch_range", "tile_size", "explicit_color_map"):
            val = data.get(var)
            if val:
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    msg = f"Could not decode value {val} for {var} as JSON"
                    raise ValidationError(msg) from exc

        val = data.get("explicit_color_map")
        if val and isinstance(val, dict):
            for key, color in val.items():
                if isinstance(color, str):
                    # convert hex strings to RGBA
                    hex_string = color.lstrip("#")
                    try:
                        rgb = [int(hex_string[i : i + 2], 16) for i in (0, 2, 4)]
                        data["explicit_color_map"][key] = (*rgb, 255)
                    except ValueError:
                        msg = f"Could not decode value {color} in explicit_color_map as hex string"
                        raise ValidationError(msg)
                elif len(color) == 3:
                    # convert RGB to RGBA
                    data["explicit_color_map"][key] = (*color, 255)

        return data


@TILE_API.route(
    "/singleband/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png",
    methods=["GET"],
)
def get_singleband(tile_z: int, tile_y: int, tile_x: int, keys: str) -> Response:
    """Return single-band PNG image of requested tile
    ---
    get:
        summary: /singleband (tile)
        description: Return single-band PNG image of requested XYZ tile
        parameters:
            - in: path
              schema: SinglebandQuerySchema
            - in: query
              schema: SinglebandOptionSchema
        responses:
            200:
                description:
                    PNG image of requested tile
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    tile_xyz = (tile_x, tile_y, tile_z)
    return _get_singleband_image(keys, tile_xyz)


class SinglebandPreviewSchema(Schema):
    keys = fields.String(
        required=True, metadata={"description": "Keys identifying dataset, in order"}
    )


@TILE_API.route("/singleband/<path:keys>/preview.png", methods=["GET"])
def get_singleband_preview(keys: str) -> Response:
    """Return single-band PNG preview image of requested dataset
    ---
    get:
        summary: /singleband (preview)
        description: Return single-band PNG preview image of requested dataset
        parameters:
            - in: path
              schema: SinglebandPreviewSchema
            - in: query
              schema: SinglebandOptionSchema
        responses:
            200:
                description:
                    PNG image of requested tile
            400:
                description:
                    Invalid query parameters
            404:
                description:
                    No dataset found for given key combination
    """
    return _get_singleband_image(keys)


def _get_singleband_image(
    keys: str, tile_xyz: Optional[Tuple[int, int, int]] = None
) -> Response:
    from terracotta.handlers.singleband import singleband

    parsed_keys = [key for key in keys.split("/") if key]

    option_schema = SinglebandOptionSchema()
    options = option_schema.load(request.args)

    if options.get("colormap", "") == "explicit":
        options["colormap"] = options.pop("explicit_color_map")

    image = singleband(parsed_keys, tile_xyz=tile_xyz, **options)

    return send_file(image, mimetype="image/png")
