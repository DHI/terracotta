"""config.py

Implement settings parsing.
"""

from typing import Mapping, Any, Tuple, NamedTuple, Dict, Optional
import os
import json
import tempfile

from marshmallow import Schema, fields, validate, pre_load, post_load, ValidationError


class TerracottaSettings(NamedTuple):
    DRIVER_PATH: str
    DRIVER_PROVIDER: Optional[str]

    DEBUG: bool
    PROFILE: bool

    RASTER_CACHE_SIZE: int
    METADATA_CACHE_SIZE: int
    TILE_SIZE: Tuple[int, int]
    DB_CACHEDIR: str


class SettingSchema(Schema):
    """Schema used to create TerracottaSettings objects"""
    DRIVER_PATH = fields.String(missing='')
    DRIVER_PROVIDER = fields.String(missing=None)

    DEBUG = fields.Boolean(missing=False)
    PROFILE = fields.Boolean(missing=False)

    RASTER_CACHE_SIZE = fields.Integer(missing=1024 * 1024 * 490)
    METADATA_CACHE_SIZE = fields.Integer(missing=1024 * 1024 * 10)

    TILE_SIZE = fields.List(fields.Integer(), validate=validate.Length(equal=2), missing=(256, 256))
    DB_CACHEDIR = fields.String(missing=os.path.join(tempfile.gettempdir(), 'terracotta'))

    @pre_load
    def prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for var in ('TILE_SIZE',):
            val = data.get(var)
            if val and isinstance(val, str):
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    raise ValidationError(f'Could not parse value for key {var} as JSON') from exc
        return data

    @post_load
    def convert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data['TILE_SIZE'] = tuple(data['TILE_SIZE'])
        return data


AVAILABLE_SETTINGS: Tuple[str, ...] = tuple(TerracottaSettings._field_types.keys())


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
