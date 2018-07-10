"""scripts/cli.py

Entry point for CLI.
"""

from typing import Any

import click


@click.group('terracotta')
def cli(*args: Any, **kwargs: Any) -> None:
    """Terracotta CLI"""
    pass


from terracotta.scripts.create_database import create_database
cli.add_command(create_database)

from terracotta.scripts.optimize_rasters import optimize_rasters
cli.add_command(optimize_rasters)

from terracotta.scripts.serve import serve
cli.add_command(serve)
