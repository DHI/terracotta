"""scripts/serve.py

Use Flask development server to serve up raster files or database locally.
"""

from typing import Any, Tuple, Sequence
import os
import tempfile
import logging

import click
import tqdm

from terracotta.scripts.click_types import RasterPattern, RasterPatternType
from terracotta.scripts.http_utils import find_open_port

logger = logging.getLogger(__name__)


@click.command('serve', short_help='Serve rasters through a local Flask development server.')
@click.option('-d', '--database', required=False, default=None, help='Database to serve from.')
@click.option('-r', '--raster-pattern', type=RasterPattern(), required=False, default=None,
              help='A format pattern defining paths and keys of the raster files to serve.')
@click.option('--rgb-key', default=None,
              help='Key to use for RGB compositing [default: last key in pattern]. '
                   'Has no effect if -r/--raster-pattern is not given.')
@click.option('--debug', is_flag=True, default=False, help='Enable Flask debugging.')
@click.option('--profile', is_flag=True, default=False, help='Enable Flask profiling.')
@click.option('--database-provider', default=None,
              help='Specify the driver to use to read database [default: auto detect].')
@click.option('--allow-all-ips', is_flag=True, default=False,
              help='Allow connections from outside IP addresses. Use with care!')
@click.option('--port', type=click.INT, default=None,
              help='Port to use [default: first free port between 5000 and 5099].')
def serve(database: str = None,
          raster_pattern: RasterPatternType = None,
          debug: bool = False,
          profile: bool = False,
          database_provider: str = None,
          allow_all_ips: bool = False,
          port: int = None,
          rgb_key: str = None) -> None:
    """Serve rasters through a local Flask development server.

    Either -d/--database or -r/--raster-pattern must be given.

    Example:

        $ terracotta serve -r /path/to/rasters/{name}/{date}_{band}_{}.tif

    The empty group {} is replaced by a wildcard matching anything (similar to * in glob patterns).

    This command is a data exploration tool and not meant for production use. Deploy Terracotta as
    a WSGI or serverless app instead.
    """
    from terracotta import get_driver, update_settings
    from terracotta.server import create_app

    if (database is None) == (raster_pattern is None):
        raise click.UsageError('Either --database or --raster-pattern must be given')

    if raster_pattern is not None:
        dbfile = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        dbfile.close()

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

        driver = get_driver(dbfile.name, provider='sqlite')
        driver.create(keys)

        with driver.connect():
            click.echo('')
            for key, filepath in tqdm.tqdm(raster_files.items(), desc="Ingesting raster files"):
                driver.insert(key, filepath, skip_metadata=True)
            click.echo('')

        database = dbfile.name

    update_settings(DRIVER_PATH=database, DRIVER_PROVIDER=database_provider,
                    DEBUG=debug, FLASK_PROFILE=profile)

    # find suitable port
    port_range = [port] if port is not None else range(5000, 5100)
    port = find_open_port(port_range)
    if port is None:
        click.echo(f'Could not find open port to bind to (ports tried: {port_range})', err=True)
        raise click.Abort()

    host = '0.0.0.0' if allow_all_ips else 'localhost'

    server_app = create_app(debug=debug, profile=profile)

    if os.environ.get('TC_TESTING'):
        return

    server_app.run(port=port, host=host, threaded=False)  # pragma: no cover
