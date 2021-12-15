"""scripts/ingest.py

A convenience tool to create a Terracotta database from some raster files.
"""

from typing import Tuple, Sequence, Any
from pathlib import Path
import logging

import click
import tqdm

from terracotta.scripts.click_types import RasterPattern, RasterPatternType, PathlibPath

logger = logging.getLogger(__name__)


@click.command('ingest',
               short_help='Ingest a collection of raster files into a SQLite database.')
@click.argument('raster-pattern', type=RasterPattern(), required=True)
@click.option('-o', '--output-file', required=True, help='Path to output file',
              type=PathlibPath(dir_okay=False, writable=True))
@click.option('--skip-metadata', is_flag=True, default=False,
              help='Speed up ingestion by skipping computation of metadata '
                   '(will be computed on first request instead)')
@click.option('--rgb-key', default=None,
              help='Key to use for RGB compositing [default: last key in pattern]')
@click.option('--skip-existing', is_flag=True, default=False,
              help='Skip existing datasets by key')
@click.option('-q', '--quiet', is_flag=True, default=False, show_default=True,
              help='Suppress all output to stdout')
def ingest(raster_pattern: RasterPatternType,
           output_file: Path,
           skip_metadata: bool = False,
           rgb_key: str = None,
           skip_existing: bool = False,
           quiet: bool = False) -> None:
    """Ingest a collection of raster files into a (new or existing) SQLite database.

    First argument is a format pattern defining paths and keys of all raster files.

    Example:

        $ terracotta create-database /path/to/rasters/{name}/{date}_{band}{}.tif -o out.sqlite

    The empty group {} is replaced by a wildcard matching anything (similar to * in glob patterns).

    Existing datasets are silently overwritten, unless you set --skip-existing.

    This command only supports the creation of a simple, local SQLite database without any
    additional metadata. For more sophisticated use cases use the Terracotta Python API.
    """
    from terracotta import get_driver

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

    if not output_file.is_file():
        driver.create(keys)

    if skip_existing:
        existing = driver.get_datasets()
        raster_files = {key: path for key, path in raster_files.items() if key not in existing}

    if tuple(keys) != driver.key_names:
        click.echo(
            f'Database file {output_file!s} has incompatible key names {driver.key_names}',
            err=True
        )
        click.Abort()

    with driver.connect():
        progress = tqdm.tqdm(raster_files.items(), desc='Ingesting raster files', disable=quiet)
        for key, filepath in progress:
            driver.insert(key, filepath, skip_metadata=skip_metadata)
