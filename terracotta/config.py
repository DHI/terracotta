from typing import Mapping, Any, Tuple, TypeVar
import os
import json
import tempfile


T = TypeVar('T', str, int, float, Tuple[str, ...], Tuple[int, ...], Tuple[float, ...])


def _coerce(from_: Any, to: T) -> T:
    """Recursively coerce first argument to type of second argument."""
    if isinstance(to, tuple):
        if len(from_) != len(to):
            raise ValueError('inconsistent length')
        return tuple(_coerce(f, t) for f, t in zip(from_, to))
    return type(to)(from_)  # type: ignore


class TerracottaSettings:
    DRIVER_PATH: str = ''
    DRIVER_PROVIDER: str = ''
    CACHE_SIZE: int = 1024 * 1024 * 500  # 500MB
    TILE_SIZE: Tuple[int, int] = (256, 256)
    DB_CACHEDIR: str = os.path.join(tempfile.gettempdir(), 'terracotta')

    __locked__: bool = False

    def __init__(self, **kwargs: Mapping[str, Any]) -> None:
        for key, val in kwargs.items():
            try:
                self.__setattr__(key, _coerce(val, getattr(self, key)))
            except (ValueError, TypeError) as exc:
                raise ValueError(f'Could not parse key {key} with value {val}') from exc

        self.__locked__ = True

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__locked__:
            raise TypeError('settings are immutable')
        object.__setattr__(self, name, value)

    def __repr__(self) -> str:
        attr_string = ', '.join(f'{key}={getattr(self, key)}' for key in AVAILABLE_SETTINGS)
        return f'TerracottaSettings({attr_string})'


AVAILABLE_SETTINGS = tuple(attr for attr in dir(TerracottaSettings) if not attr.startswith('_'))


def parse_config(config: Mapping[str, Any] = None) -> TerracottaSettings:
    """Parse given config dict and return new TerracottaSettings object"""
    config_dict = config or {}

    def get_value(key: str) -> Tuple[str, Any]:
        value = config_dict.get(key)

        if value is None:
            env_value = os.environ.get(f'TC_{key}', None)
            if env_value:
                try:
                    value = json.loads(env_value)
                except json.decoder.JSONDecodeError as exc:
                    raise ValueError(f'Could not parse environment variable TC_{key} with value'
                                     f'{env_value} as JSON') from exc

        return key, value

    parsed_settings = dict((key, value) for key, value in map(get_value, AVAILABLE_SETTINGS)
                           if value)
    new_settings = TerracottaSettings(**parsed_settings)
    return new_settings
