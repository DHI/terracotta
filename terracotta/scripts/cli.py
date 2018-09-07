"""scripts/cli.py

Entry point for CLI.
"""

from typing import Any

import click

from terracotta import logs


@click.group('terracotta', invoke_without_command=True)
@click.option('--loglevel', help='Set level for log messages', default=None,
              type=click.Choice(['trace', 'debug', 'info', 'warning', 'error', 'critical']))
@click.pass_context
def cli(ctx: click.Context, *args: Any, loglevel: str = None, **kwargs: Any) -> None:
    """Terracotta CLI"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

    if loglevel is not None:
        logs.set_logger(level=loglevel)


from terracotta.scripts.create_database import create_database
cli.add_command(create_database)

from terracotta.scripts.optimize_rasters import optimize_rasters
cli.add_command(optimize_rasters)

from terracotta.scripts.serve import serve
cli.add_command(serve)
