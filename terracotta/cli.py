import itertools
import glob
import os

import click

import terracotta.app as app


class GlobbityGlob(click.ParamType):
    name = 'glob'

    def convert(self, value, *args):
        return glob.glob(value)


class ExpandedPath(click.Path):
    def convert(self, value, *args, **kwargs):
        if os.name == 'nt':
            # Only expand on Windows, as shell will do it on *nix
            value = os.path.expanduser(value)
        return super().convert(value, *args, **kwargs)


@click.command()
@click.option('--debug', is_flag=True, default=False,
              help='Enable Flask debugging')
@click.option('--profile', is_flag=True, default=False,
              help='Enable Flask profiling')
@click.option('-p', '--preview', is_flag=True, default=False,
              help='Open preview in browser (implies debug)')
@click.option('--cfg-file', '-c', type=ExpandedPath(exists=True), default=None)
@click.argument('raster_files', nargs=-1, type=GlobbityGlob(), required=False)
def cli(raster_files, cfg_file, *args, **kwargs):
    """Entry point of Terracotta CLI"""
    # flatten before usage
    if not raster_files and not cfg_file:
        raise click.UsageError('Either pass a --cfg-file or a list of raster files')
    raster_files = itertools.chain.from_iterable(raster_files)
    kwargs['debug'] = kwargs['preview'] or kwargs['debug']
    app.run_app(raster_files, cfg_file, *args, **kwargs)
