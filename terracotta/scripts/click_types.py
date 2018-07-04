import pathlib
import glob
import re
import os
import string

import click


class GlobbityGlob(click.ParamType):
    name = 'glob'

    def convert(self, value, *args):
        return [pathlib.Path(f) for f in glob.glob(value)]


class PathlibPath(click.Path):
    def convert(self, *args, **kwargs):
        return pathlib.Path(super(PathlibPath, self).convert(*args, **kwargs))


class RasterPattern(click.ParamType):
    """Expands a pattern following the Python format specification to matching files"""
    name = 'raster-pattern'

    def convert(self, value, *args, **kwargs):
        value = os.path.realpath(value).replace('\\', '\\\\')

        try:
            parsed_value = list(string.Formatter().parse(value))
        except ValueError as exc:
            self.fail(f'Invalid pattern: {exc!s}')

        # extract keys from format string and assemble glob and regex patterns matching it
        keys = [field_name for _, field_name, _, _ in parsed_value if field_name]
        glob_pattern = value.format(**{k: '*' for k in keys})
        regex_pattern = value.format(**{k: f'(?P<{k}>\\w+)' for k in keys})

        if not keys:
            self.fail('Pattern must contain at least one placeholder')

        try:
            regex_pattern = re.compile(regex_pattern)
        except re.error as exc:
            self.fail(f'Could not parse pattern to regex: {exc!s}')

        # use glob to find candidates, regex to extract placeholder values
        candidates = [os.path.realpath(candidate) for candidate in glob.glob(glob_pattern)]
        matched_candidates = [regex_pattern.match(candidate) for candidate in candidates]

        key_combinations = [tuple(match.groups()) for match in matched_candidates if match]
        if len(key_combinations) != len(set(key_combinations)):
            self.fail('Pattern leads to duplicate keys')

        files = {tuple(match.groups()): match.group(0) for match in matched_candidates if match}
        return keys, files


class TOMLFile(click.ParamType):
    name = 'toml-file'

    def convert(self, value, *args, **kwargs):
        import toml
        return toml.load(value)
