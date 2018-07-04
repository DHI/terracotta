import click


@click.group('terracotta')
def cli(*args, **kwargs):
    """Terracotta CLI"""
    pass


from terracotta.scripts.create_database import create_database
cli.add_command(create_database)

from terracotta.scripts.optimize_rasters import optimize_rasters
cli.add_command(optimize_rasters)

from terracotta.scripts.serve import serve
cli.add_command(serve)
