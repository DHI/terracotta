"""scripts/create_database.py

A convenience tool to create a Terracotta database from some raster files.
"""

from typing import Tuple, Sequence, Any
from pathlib import Path

import click

from terracotta.scripts.click_utils import RasterPattern, RasterPatternType, PathlibPath


@click.command('create-database',
               short_help='Create a new SQLite raster database from a collection of raster files.')
@click.argument('raster-pattern', type=RasterPattern(), required=True)
@click.option('-o', '--output-file', type=PathlibPath(dir_okay=False), required=True,
              help='Path to output file.')
@click.option('--overwrite', is_flag=True, default=False,
              help='Always overwrite existing database without asking')
@click.option('--skip-metadata', is_flag=True, default=False,
              help='Speed up ingestion by not pre-computing metadata '
                   '(will be computed on first request instead)')
@click.option('--rgb-key', default=None,
              help='Key to use for RGB compositing [default: last key in pattern]')
def create_database(raster_pattern: RasterPatternType,
                    output_file: Path,
                    overwrite: bool = False,
                    skip_metadata: bool = False,
                    rgb_key: str = None) -> None:
    """Create a new SQLite raster database from a collection of raster files.

    First arguments is a format pattern defining paths and keys of all raster files.

    Example:

        terracotta create-database /path/to/rasters/{name}/{date}_{band}.tif -o out.sqlite

    This command only supports the creation of a simple SQLite database without any additional
    metadata. For more sophisticated use cases use the Terracotta Python API.
    """
    from terracotta import get_driver

    if output_file.is_file() and not overwrite:
        click.confirm(f'Output file {output_file} exists. Continue?', abort=True)

    keys, raster_files = raster_pattern

    if rgb_key is not None:
        if rgb_key not in keys:
            raise click.UsageError('RGB key not found in raster pattern')

        # re-order keys
        rgb_idx = keys.index(rgb_key)

        def push_to_last(seq: Sequence[Any], index: int) -> Tuple[Any, ...]:
            return (*seq[:index], *seq[index + 1:], seq[index])

        keys = list(push_to_last(keys, rgb_idx))
        raster_files = {push_to_last(k, rgb_idx): v for k, v in raster_files.items()}

    driver = get_driver(output_file)

    pbar_args = dict(
        label='Ingesting raster files',
        show_eta=False,
        item_show_func=lambda item: item[1] if item else ''
    )

    with driver.connect():
        driver.create(keys, drop_if_exists=True)

        click.echo('')
        with click.progressbar(raster_files.items(), **pbar_args) as pbar:  # type: ignore
            for key, filepath in pbar:
                driver.insert(key, filepath, compute_metadata=not skip_metadata)
