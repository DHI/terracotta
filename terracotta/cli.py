import itertools
import glob
import click

import terracotta.app as app


class GlobbityGlob(click.ParamType):
    name = 'glob'

    def convert(self, value, *args):
        return glob.glob(value)


@click.command()
@click.option('--debug', is_flag=True, default=False,
              help='Enable Flask debugging')
@click.option('--profile', is_flag=True, default=False,
              help='Enable Flask profiling')
@click.option('--cfg-file', type=click.Path(exists=True), default=None, required=False)
@click.option('-p', '--preview', is_flag=True, default=False,
              help='Open preview in browser (implies debug)')
@click.argument('raster_files', nargs=-1, type=GlobbityGlob(), required=False)
def cli(raster_files, *args, **kwargs):
    """Entry point of Terracotta CLI"""
    # flatten before usage
    raster_files = itertools.chain.from_iterable(raster_files)
    kwargs['debug'] = kwargs['preview'] or kwargs['debug']
    app.run_app(raster_files, *args, **kwargs)
