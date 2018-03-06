import click

import terracotta.app as app


@click.command()
@click.option('--debug', is_flag=True, default=False,
              help='Enable Flask debugging')
def cli(debug):
    '''Entry point of terracotta CLI'''
    app.run_app(debug)
