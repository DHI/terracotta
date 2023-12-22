import re
from marshmallow import ValidationError, fields

from typing import Any


class StringOrNumber(fields.Field):
    def _serialize(
        self, value: Any, attr: Any, obj: Any, **kwargs: Any
    ) -> str | float | None:
        if isinstance(value, (str, bytes)):
            return fields.String()._serialize(value, attr, obj, **kwargs)
        elif isinstance(value, (int, float)):
            return fields.Float()._serialize(value, attr, obj, **kwargs)
        else:
            raise ValidationError("Must be a string or a number")

    def _deserialize(
        self, value: Any, attr: Any, data: Any, **kwargs: Any
    ) -> str | float | None:
        if isinstance(value, (str, bytes)):
            return fields.String()._deserialize(value, attr, data, **kwargs)
        elif isinstance(value, (int, float)):
            return fields.Float()._deserialize(value, attr, data, **kwargs)
        else:
            raise ValidationError("Must be a string or a number")


def validate_stretch_range(data: Any) -> None:
    if isinstance(data, str) and data.startswith("p"):
        if not re.match("^p\\d+$", data):
            raise ValidationError("Percentile format is `p<digits>`")
    else:
        try:
            float(data)
        except ValueError:
            raise ValidationError("Must be a number")
