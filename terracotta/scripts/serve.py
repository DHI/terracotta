"""scripts/serve.py

Use Flask development server to serve up raster files or database locally.
"""

from typing import Mapping, Any, Tuple, Sequence
import tempfile

import click

from terracotta.scripts.click_utils import RasterPattern, RasterPatternType, TOMLFile


@click.command('serve', short_help='Serve rasters through a local Flask development server.')
@click.option('-d', '--database', required=False, default=None, help='Database to serve from.')
@click.option('-r', '--raster-pattern', type=RasterPattern(), required=False, default=None,
              help='A format pattern defining paths and keys of the raster files to serve.')
@click.option('-c', '--config', type=TOMLFile(), default=None,
              help='Update global settings from this TOML file.')
@click.option('--rgb-key', default=None,
              help='Key to use for RGB compositing [default: last key in pattern]. '
                   'Has no effect if -r/--raster-pattern is not given.')
@click.option('--no-browser', is_flag=True, default=False, help='Do not serve preview page.')
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
          no_browser: bool = False,
          config: Mapping[str, Any] = None,
          database_provider: str = None,
          allow_all_ips: bool = False,
          port: int = None,
          rgb_key: str = None) -> None:
    """Serve rasters through a local Flask development server.

    Either --database or --raster-pattern must be given.

    Example:

        terracotta serve -r /path/to/rasters/{name}/{date}_{band}.tif

    This command is a data exploration tool and not meant for production use. Deploy Terracotta as
    a WSGI or serverless app instead.
    """
    from terracotta import get_driver, update_settings
    from terracotta.api import run_app

    if config is not None:
        update_settings(**config)

    if (database is None) == (raster_pattern is None):
        raise click.UsageError('Either --database or --raster-pattern must be given')

    if raster_pattern is not None:
        dbfile = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        dbfile.close()

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

        driver = get_driver(dbfile.name, provider='sqlite')

        pbar_args = dict(
            label='Ingesting raster files',
            show_eta=False,
            item_show_func=lambda item: item[1] if item else ''
        )

        with driver.connect():
            driver.create(keys)

            click.echo('')
            with click.progressbar(raster_files.items(), **pbar_args) as pbar:  # type: ignore
                for key, filepath in pbar:
                    driver.insert(key, filepath, skip_metadata=True)
            click.echo('')

        database = dbfile.name

    update_settings(DRIVER_PATH=database, DRIVER_PROVIDER=database_provider,
                    DEBUG=debug, FLASK_PROFILE=profile)

    # find open port
    def check_socket(host: str, port: int) -> bool:
        """Check if given port can be listened to"""
        import socket
        from contextlib import closing

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(2)
            try:
                sock.bind((host, port))
                sock.listen(1)
                return True
            except socket.error:
                return False

    port_range = [port] if port is not None else range(5000, 5100)
    for port_candidate in port_range:
        if check_socket('localhost', port_candidate):
            port = port_candidate
            break
    else:
        click.echo(f'Could not find open port to bind to (ports tried: {port_range})')
        raise click.Abort()

    run_app(port=port, allow_all_ips=allow_all_ips, debug=debug,
            flask_profile=profile, preview=not no_browser)
