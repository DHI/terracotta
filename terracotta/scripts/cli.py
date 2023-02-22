"""scripts/cli.py

Entry point for CLI.
"""

from typing import Any, Mapping
import sys

import click

from terracotta.scripts.click_types import TOMLFile
from terracotta import get_settings, update_settings, logs, __version__


@click.group('terracotta', invoke_without_command=True)
@click.option('-c', '--config', type=TOMLFile(), default=None,
              help='Update global settings from this TOML file.')
@click.option('--loglevel', help='Set level for log messages', default=None,
              type=click.Choice(['debug', 'info', 'warning', 'error', 'critical']))
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx: click.Context,
        config: Mapping[str, Any] = None,
        loglevel: str = None) -> None:
    """The command line interface for the Terracotta tile server.

    All flags must be passed before specifying a subcommand.

    Example:

        $ terracotta -c config.toml connect localhost:5000

    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

    # update settings from config file
    if config is not None:
        update_settings(**config)

    # setup logging
    settings = get_settings()

    if loglevel is None:
        loglevel = settings.LOGLEVEL

    logs.set_logger(loglevel, catch_warnings=True)


def entrypoint() -> None:
    try:
        cli(obj={})
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('Uncaught exception!', exc_info=True)
        sys.exit(1)


from terracotta.scripts.connect import connect
cli.add_command(connect)

from terracotta.scripts.ingest import ingest
cli.add_command(ingest)

from terracotta.scripts.optimize_rasters import optimize_rasters
cli.add_command(optimize_rasters)

from terracotta.scripts.serve import serve
cli.add_command(serve)


if __name__ == '__main__':
    entrypoint()
