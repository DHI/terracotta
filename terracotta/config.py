from typing import Mapping, Any
import collections
import os
import json


Setting = collections.namedtuple('Setting', ['type', 'default'])

CONFIG_SCHEMA = {
    'CACHE_SIZE': Setting(int, 1024 * 1024 * 500),  # 500MB
    'TILE_SIZE': Setting([int, int], (256, 256))
}

TerracottaSettings = collections.namedtuple('TerracottaSettings', list(CONFIG_SCHEMA.keys()))


def get_settings(config: Mapping[str, Any] = None):
    """Parse given config dict and return new TerracottaSettings object"""
    if config is None:
        config = {}

    def get_value(key: str, value: Any):
        key = key.upper()
        if key not in CONFIG_SCHEMA:
            raise ValueError(f'Unrecognized setting {key}')
        setting = CONFIG_SCHEMA[key]

        if value is None:
            env_value = os.environ.get(f'TC_{key}', None)
            if env_value:
                value = json.loads(env_value)
            else:
                value = setting.default

        if isinstance(setting.type, collections.Iterable):
            if len(setting.type) != len(value):
                raise ValueError(f'Expected {len(setting.type)} values for setting {key}, '
                                 f'got {len(value)}')
            return tuple(type_fun(subvalue) for type_fun, subvalue in zip(setting.type, value))

        return setting.type(value)

    new_settings = TerracottaSettings(
        **{key: get_value(key, config.get(key)) for key in CONFIG_SCHEMA.keys()}
    )
    return new_settings
