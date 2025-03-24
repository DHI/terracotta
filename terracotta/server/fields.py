"""server/fields.py

Custom marshmallow fields for the server API.
"""

import re
from marshmallow import ValidationError, fields

from typing import Any, Union

import numpy as np
from color_operations import parse_operations


class StringOrNumber(fields.Field):
    """
    Marshmallow type that can be either a string or a number.
    Uses marshmallow's default serialization/deserialization
    for `String` or a `Float` depending on the value type.
    """

    def _serialize(
        self, value: Union[str, bytes, int, float], attr: Any, obj: Any, **kwargs: Any
    ) -> Union[str, float, None]:
        if isinstance(value, (str, bytes)):
            return fields.String()._serialize(value, attr, obj, **kwargs)
        elif isinstance(value, (int, float)):
            return fields.Float()._serialize(value, attr, obj, **kwargs)
        else:
            raise ValidationError("Must be a string or a number")

    def _deserialize(
        self, value: Union[str, bytes, int, float], attr: Any, data: Any, **kwargs: Any
    ) -> Union[str, float, None]:
        if isinstance(value, (str, bytes)):
            return fields.String()._deserialize(value, attr, data, **kwargs)
        elif isinstance(value, (int, float)):
            return fields.Float()._deserialize(value, attr, data, **kwargs)
        else:
            raise ValidationError("Must be a string or a number")


def validate_stretch_range(data: Any) -> None:
    """
    Validates that the stretch range is in the format `p<digits>`
    when a string is used.
    """
    if isinstance(data, str):
        if not re.match("^p\\d+$", data):
            raise ValidationError("Percentile format is `p<digits>`")


def validate_color_transform(data: Any, test_array_bands: int) -> None:
    """
    Validate that the color transform is a string and can be parsed by `color_operations`.
    """
    if not isinstance(data, str):
        raise ValidationError("Color transform needs to be a string")

    try:
        ops = parse_operations(data)
    except (ValueError, KeyError):
        raise ValidationError("Invalid color transform")

    test_array = np.ones((test_array_bands, 1, 1))
    try:
        for op in ops:
            test_array = op(test_array)
    except (ValueError, TypeError, IndexError):
        raise ValidationError("Invalid color transform")
