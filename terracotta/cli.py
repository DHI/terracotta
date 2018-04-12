import os

import click

import terracotta.app as app


class ExpandedPath(click.Path):
    def convert(self, value, *args, **kwargs):
        if os.name == 'nt':
            # Only expand on Windows, as shell will do it on *nix
            value = os.path.expanduser(value)
        return super().convert(value, *args, **kwargs)


@click.command()
@click.option('--debug', is_flag=True, default=False,
              help='Enable Flask debugging')
@click.option('--cfg-file', '-c', type=ExpandedPath(exists=True), default='./config.cfg')
def cli(debug, cfg_file):
    """Entry point of terracotta CLI"""
    app.run_app(cfg_file, debug)
