import click

import terracotta.app as app


@click.command()
@click.option('--debug', is_flag=True, default=False,
              help='Enable Flask debugging')
@click.option('--profile', is_flag=True, default=False,
              help='Enable Flask profiling')
@click.option('--cfg-file', type=click.Path(exists=True), default='./config.cfg')
def cli(*args, **kwargs):
    """Entry point of terracotta CLI"""
    app.run_app(*args, **kwargs)
