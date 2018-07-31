"""scripts/cli.py

Entry point for CLI.
"""

from typing import Any, Dict
import sys

import click


@click.group('terracotta')
@click.pass_context
def cli(ctx: click.Context, *args: Any, **kwargs: Any) -> None:
    """Terracotta CLI"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


from terracotta.scripts.create_database import create_database
cli.add_command(create_database)

from terracotta.scripts.optimize_rasters import optimize_rasters
cli.add_command(optimize_rasters)

from terracotta.scripts.serve import serve
cli.add_command(serve)


def entrypoint() -> None:
    obj: Dict = {}
    try:
        cli(obj=obj)
    except KeyboardInterrupt:
        click.echo('Aborted!', err=True)
        sys.exit(1)
    except Exception as exc:
        styled_prefix = click.style('Error', fg='red', bg='white', bold=True)
        error_string = f'\n{styled_prefix}\n{exc!s}'
        click.echo(error_string, err=True)
        sys.exit(1)
