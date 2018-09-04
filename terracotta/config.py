"""config.py

Implement settings parsing.
"""

from typing import Mapping, Any, Tuple, NamedTuple, Dict, Optional
import os
import json
import tempfile

from marshmallow import Schema, fields, validate, pre_load, post_load, ValidationError


class TerracottaSettings(NamedTuple):
    DRIVER_PATH: str = ''
    DRIVER_PROVIDER: Optional[str] = None

    DEBUG: bool = False
    FLASK_PROFILE: bool = False
    XRAY_PROFILE: bool = False

    RASTER_CACHE_SIZE: int = 1024 * 1024 * 490  # 490 MB
    METADATA_CACHE_SIZE: int = 1024 * 1024 * 10  # 10 MB

    TILE_SIZE: Tuple[int, int] = (256, 256)
    PNG_COMPRESS_LEVEL: int = 1

    DB_CACHEDIR: str = os.path.join(tempfile.gettempdir(), 'terracotta')
    DB_CONNECTION_TIMEOUT: int = 10

    UPSAMPLING_METHOD: str = 'nearest'
    DOWNSAMPLING_METHOD: str = 'average'


AVAILABLE_SETTINGS: Tuple[str, ...] = tuple(TerracottaSettings._field_types.keys())


class SettingSchema(Schema):
    """Schema used to create TerracottaSettings objects"""
    DRIVER_PATH = fields.String()
    DRIVER_PROVIDER = fields.String(allow_none=True)

    DEBUG = fields.Boolean()
    FLASK_PROFILE = fields.Boolean()
    XRAY_PROFILE = fields.Boolean()

    RASTER_CACHE_SIZE = fields.Integer()
    METADATA_CACHE_SIZE = fields.Integer()

    TILE_SIZE = fields.List(fields.Integer(), validate=validate.Length(equal=2))
    PNG_COMPRESS_LEVEL = fields.Integer(validate=validate.Range(min=0, max=9))

    DB_CACHEDIR = fields.String()
    DB_CONNECTION_TIMEOUT = fields.Integer()

    UPSAMPLING_METHOD = fields.String(
        validate=validate.OneOf(['nearest', 'linear', 'cubic', 'average'])
    )
    DOWNSAMPLING_METHOD = fields.String(
        validate=validate.OneOf(['nearest', 'linear', 'cubic', 'average'])
    )

    @pre_load
    def decode_lists(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for var in ('TILE_SIZE',):
            val = data.get(var)
            if val and isinstance(val, str):
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    raise ValidationError(f'Could not parse value for key {var} as JSON') from exc
        return data

    @post_load
    def encode_tuples(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for var in ('TILE_SIZE',):
            val = data.get(var)
            if val:
                data[var] = tuple(val)
        return data


def parse_config(config: Mapping[str, Any] = None) -> TerracottaSettings:
    """Parse given config dict and return new TerracottaSettings object"""
    config_dict = dict(config or {})

    for setting in AVAILABLE_SETTINGS:
        env_setting = f'TC_{setting}'
        if setting not in config_dict and env_setting in os.environ:
            config_dict[setting] = os.environ[env_setting]

    schema = SettingSchema()
    try:
        parsed_settings = schema.load(config_dict)
    except ValidationError as exc:
        raise ValueError('Could not parse configuration') from exc

    new_settings = TerracottaSettings(**parsed_settings)
    return new_settings
