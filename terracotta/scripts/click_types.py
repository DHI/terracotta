"""scripts/click_types.py

Custom click parameter types and utilities.
"""

from typing import List, Any, Tuple, Dict
import pathlib
import glob
import re
import os
import string

import click


class GlobbityGlob(click.ParamType):
    """Expands a glob pattern to Path objects"""
    name = 'glob'

    def convert(self, value: str, *args: Any) -> List[pathlib.Path]:
        return [pathlib.Path(f) for f in glob.glob(value)]


class PathlibPath(click.Path):
    """Converts a string to a pathlib.Path object"""

    def convert(self, *args: Any) -> pathlib.Path:
        return pathlib.Path(super().convert(*args))


RasterPatternType = Tuple[List[str], Dict[Tuple[str, ...], str]]


def _parse_raster_pattern(raster_pattern: str) -> Tuple[List[str], str, str]:
    """Parse a raster pattern string using Python format syntax.

    Extracts names of unique placeholders, a glob pattern
    and a regular expression to retrieve files matching the given pattern.

    Example:

        >>> _parse_raster_pattern('{key1}/{key2}_{}.tif')
        (['key1', 'key2'], '*/*_*.tif', '(?P<key1>[^\\W_]+)/(?P<key2>[^\\W_]+)_.*?\\.tif')

    """

    # raises ValueError on invalid patterns
    parsed_value = string.Formatter().parse(raster_pattern)

    keys: List[str] = []
    glob_pattern: List[str] = []
    regex_pattern: List[str] = []

    for before_field, field_name, _, _ in parsed_value:
        glob_pattern += before_field
        regex_pattern += re.escape(before_field)

        if field_name is None:
            # no placeholder
            continue

        glob_pattern.append('*')

        if field_name == '':
            # unnamed placeholder
            regex_pattern.append('.*?')
        elif field_name in keys:
            # duplicate placeholder
            key_group_number = keys.index(field_name) + 1
            regex_pattern.append(rf'\{key_group_number}')
        else:
            # new placeholder
            keys.append(field_name)
            regex_pattern += rf'(?P<{field_name}>[^\W_]+)'

    return keys, ''.join(glob_pattern), ''.join(regex_pattern)


class RasterPattern(click.ParamType):
    """Expands a pattern following the Python format specification to matching files"""
    name = 'raster-pattern'

    def convert(self, value: str, *args: Any) -> RasterPatternType:
        value = os.path.abspath(value)
        try:
            keys, glob_pattern, regex_pattern = _parse_raster_pattern(value)
        except ValueError as exc:
            self.fail(f'Invalid pattern: {exc!s}')

        if not keys:
            self.fail('Pattern must contain at least one placeholder')

        if not all(re.match(r'\w', key) for key in keys):
            self.fail('Key names must be alphanumeric')

        # use glob to find candidates, regex to extract placeholder values
        candidates = (os.path.abspath(c) for c in glob.glob(glob_pattern))
        matched_candidates = [re.match(regex_pattern, candidate) for candidate in candidates]

        if not any(matched_candidates):
            self.fail('Given pattern matches no files')

        key_combinations = [tuple(match.groups()) for match in matched_candidates if match]
        if len(key_combinations) != len(set(key_combinations)):
            self.fail('Pattern leads to duplicate keys')

        files = {tuple(match.groups()): match.group(0) for match in matched_candidates if match}
        return keys, files


class TOMLFile(click.ParamType):
    """Parses a TOML file to a dict"""
    name = 'toml-file'

    def convert(self, value: str, *args: Any) -> Dict[str, Any]:
        import toml
        return dict(toml.load(value))


class Hostname(click.ParamType):
    """Parses a string to a valid hostname"""
    name = 'url'

    def __init__(self, default_port: int = 5000, default_scheme: str = 'http') -> None:
        self.default_port = default_port
        self.default_scheme = default_scheme

    def convert(self, value: str, *args: Any) -> str:
        from urllib.parse import urlparse, urlunparse
        parsed_url = urlparse(value)

        if not parsed_url.netloc:
            value_with_scheme = '://'.join([self.default_scheme, value])
            parsed_url = urlparse(value_with_scheme)

        # remove everything we don't need
        return urlunparse([parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''])
