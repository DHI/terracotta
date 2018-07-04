import tempfile

import click

from terracotta.scripts.click_types import RasterPattern, TOMLFile


@click.command('serve')
@click.option('-d', '--database', required=False, default=None)
@click.option('-r', '--raster-pattern', type=RasterPattern(), required=False, default=None)
@click.option('-c', '--config', type=TOMLFile(), default=None)
@click.option('--no-browser', is_flag=True, default=False)
@click.option('--debug', is_flag=True, default=False,
              help='Enable Flask debugging')
@click.option('--profile', is_flag=True, default=False,
              help='Enable Flask profiling')
@click.option('--database-provider', default=None)
@click.option('--allow-all-ips', is_flag=True, default=False,
              help='Allow connections from outside IP addresses')
@click.option('--port', type=click.INT, default=None,
              help='Port to use [default: first free port between 5000 and 5099]')
def serve(database=None, raster_pattern=None, debug=False, profile=False, no_browser=False,
          config=None, database_provider=None, allow_all_ips=False, port=None):
    from terracotta import get_driver, update_settings
    from terracotta.flask_api import run_app

    if config is not None:
        update_settings(config)

    if (database is None) == (raster_pattern is None):
        raise click.UsageError('Either --database or --raster-pattern must be given')

    if database is None:
        dbfile = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        dbfile.close()

        keys, raster_files = raster_pattern
        driver = get_driver(dbfile.name, provider='sqlite')

        with driver.connect():
            driver.create(keys)
            for key, filepath in raster_files.items():
                driver.insert(key, filepath, compute_metadata=False)

        database = dbfile.name

    update_settings({'DRIVER_PATH': database, 'DRIVER_PROVIDER': database_provider})

    # find open port
    def check_socket(host, port):
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
        raise click.ClickException(f'Could not find open port to bind to '
                                   f'(ports tried: {port_range})')

    run_app(port=port, allow_all_ips=allow_all_ips, debug=debug, profile=profile,
            preview=not no_browser)
