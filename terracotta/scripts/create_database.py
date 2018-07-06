from pathlib import Path

import click

from terracotta.scripts.click_types import RasterPattern, RasterPatternType, PathlibPath


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
def create_database(raster_pattern: RasterPatternType, output_file: Path,
                    overwrite: bool = False, skip_metadata: bool = False) -> None:
    """Create a new SQLite raster database from a collection of raster files.

    First arguments is a format pattern defining paths and keys of all raster files.

    Example:

        terracotta create-database /path/to/rasters/{{name}}/{{date}}_{{band}}.tif -o out.sqlite

    This command only supports the creation of a simple SQLite database without any additional
    metadata. For more sophisticated use cases use the Terracotta Python API.
    """
    import tqdm
    from terracotta import get_driver

    if output_file.is_file() and not overwrite:
        click.confirm(f'Output file {output_file} exists. Continue?', abort=True)

    keys, raster_files = raster_pattern
    driver = get_driver(output_file)
    pbar = tqdm.tqdm(raster_files.items())

    with driver.connect():
        driver.create(keys, drop_if_exists=True)
        for key, filepath in pbar:
            pbar.set_postfix({'file': filepath})
            driver.insert(key, filepath, compute_metadata=not skip_metadata)
