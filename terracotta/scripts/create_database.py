"""scripts/create_database.py

A convenience tool to create a Terracotta database from some raster files.
"""

from typing import Tuple, Sequence, Any
from pathlib import Path
import logging

import click
import tqdm

from terracotta.scripts.click_utils import RasterPattern, RasterPatternType, PathlibPath

logger = logging.getLogger(__name__)


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
@click.option('-q', '--quiet', is_flag=True, default=False, show_default=True,
              help='Suppress all output to stdout')
def create_database(raster_pattern: RasterPatternType,
                    output_file: Path,
                    overwrite: bool = False,
                    skip_metadata: bool = False,
                    rgb_key: str = None,
                    quiet: bool = False) -> None:
    """Create a new SQLite raster database from a collection of raster files.

    First arguments is a format pattern defining paths and keys of all raster files.

    Example:

        terracotta create-database /path/to/rasters/{name}/{date}_{band}.tif -o out.sqlite

    This command only supports the creation of a simple SQLite database without any additional
    metadata. For more sophisticated use cases use the Terracotta Python API.
    """
    from terracotta import get_driver

    if output_file.is_file() and not overwrite:
        click.confirm(f'Existing output file {output_file} will be overwritten. Continue?',
                      abort=True)
        output_file.unlink()

    keys, raster_files = raster_pattern

    if rgb_key is not None:
        if rgb_key not in keys:
            raise click.BadParameter('RGB key not found in raster pattern')

        # re-order keys
        rgb_idx = keys.index(rgb_key)

        def push_to_last(seq: Sequence[Any], index: int) -> Tuple[Any, ...]:
            return (*seq[:index], *seq[index + 1:], seq[index])

        keys = list(push_to_last(keys, rgb_idx))
        raster_files = {push_to_last(k, rgb_idx): v for k, v in raster_files.items()}

    driver = get_driver(output_file)
    driver.create(keys)

    with driver.connect():
        progress = tqdm.tqdm(raster_files.items(), desc='Ingesting raster files', disable=quiet)
        for key, filepath in progress:
            driver.insert(key, filepath, skip_metadata=skip_metadata)
