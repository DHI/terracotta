"""scripts/connect.py

Use Flask development server to serve Terracotta client app.
"""

import threading
import webbrowser

import click
import requests

from terracotta.scripts.click_utils import Hostname
from terracotta.scripts.http_utils import find_open_port


@click.command(
    'connect',
    short_help=(
        'Connect to a running Terracotta instance and interactively '
        'explore data in it. First argument is hostname and port to connect '
        'to (e.g. localhost:5000).'
    )
)
@click.argument('terracotta-hostname', required=True, type=Hostname())
@click.option('--no-browser', is_flag=True, default=False, help='Do not open browser')
@click.option('--port', type=click.INT, default=None,
              help='Port to use [default: first free port between 5100 and 5199].')
def connect(terracotta_hostname: str, no_browser: bool = False, port: int = None) -> None:
    """Connect to a running Terracotta and interactively explore data in it."""
    from terracotta.client.flask_api import run_app

    test_url = f'{terracotta_hostname}/keys'

    with requests.get(test_url) as response:
        if not response.status_code == 200:
            click.echo(
                f'Could not connect to {test_url}, check hostname and ensure '
                'that Terracotta is running on the server', err=True
            )
            raise click.Abort()

    # find suitable port
    port_range = [port] if port is not None else range(5100, 5200)
    port = find_open_port(port_range)
    if port is None:
        click.echo(f'Could not find open port to bind to (ports tried: {port_range})', err=True)
        raise click.Abort()

    def open_browser() -> None:
        webbrowser.open(f'http://127.0.0.1:{port}/')

    if not no_browser:
        threading.Timer(2, open_browser).start()

    run_app(terracotta_hostname, port=port)
