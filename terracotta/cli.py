import itertools
import pathlib
import glob
import re
import tempfile
import os
import string

import click


class GlobbityGlob(click.ParamType):
    name = 'glob'

    def convert(self, value, *args):
        return [pathlib.Path(f) for f in glob.glob(value)]


class PathlibPath(click.Path):
    def convert(self, *args, **kwargs):
        return pathlib.Path(super(PathlibPath, self).convert(*args, **kwargs))


class RasterPattern(click.ParamType):
    """Expands a pattern following the Python format specification to matching files"""
    name = 'raster-pattern'

    def convert(self, value, *args, **kwargs):
        value = os.path.realpath(value).replace('\\', '\\\\')

        try:
            parsed_value = list(string.Formatter().parse(value))
        except ValueError as exc:
            self.fail(f'Invalid pattern: {exc!s}')

        # extract keys from format string and assemble glob and regex patterns matching it
        keys = [field_name for _, field_name, _, _ in parsed_value if field_name]
        glob_pattern = value.format(**{k: '*' for k in keys})
        regex_pattern = value.format(**{k: f'(?P<{k}>\\w+)' for k in keys})

        if not keys:
            self.fail('Pattern must contain at least one placeholder')

        try:
            regex_pattern = re.compile(regex_pattern)
        except re.error as exc:
            self.fail(f'Could not parse pattern to regex: {exc!s}')

        # use glob to find candidates, regex to extract placeholder values
        candidates = [os.path.realpath(candidate) for candidate in glob.glob(glob_pattern)]
        matched_candidates = [regex_pattern.match(candidate) for candidate in candidates]

        key_combinations = [tuple(match.groups()) for match in matched_candidates if match]
        if len(key_combinations) != len(set(key_combinations)):
            self.fail('Pattern leads to duplicate keys')

        files = {tuple(match.groups()): match.group(0) for match in matched_candidates if match}
        return keys, files


class TOMLFile(click.ParamType):
    name = 'toml-file'

    def convert(self, value, *args, **kwargs):
        import toml
        return toml.load(value)


@click.group('terracotta')
def cli(*args, **kwargs):
    """Entry point of Terracotta CLI"""
    pass


@cli.command('serve')
@click.option('-d', '--database', required=False, default=None)
@click.option('-r', '--raster-pattern', type=RasterPattern(), required=False, default=None)
@click.option('--no-browser', is_flag=True, default=False)
@click.option('--debug', is_flag=True, default=False,
              help='Enable Flask debugging')
@click.option('--profile', is_flag=True, default=False,
              help='Enable Flask profiling')
@click.option('-c', '--config', type=TOMLFile(), default=None)
@click.option('--database-provider', default=None)
def serve(database=None, raster_pattern=None, debug=False, profile=False, no_browser=False,
          config=None, database_provider=None):
    from terracotta import get_driver, update_settings
    from terracotta.flask_api import run_app

    if config is not None:
        update_settings(config)

    if (database is None) == (raster_pattern is None):
        raise click.UsageError('Either --database or --raster-pattern must be given')

    if database is None:
        dbfile = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        dbfile.close()

        keys, raster_files = raster_pattern
        driver = get_driver(dbfile.name, provider='sqlite')

        with driver.connect():
            driver.create(keys)
            for key, filepath in raster_files.items():
                driver.insert(key, filepath, compute_metadata=False)
    else:
        driver = get_driver(database, provider=database_provider)

    run_app(driver, debug=debug, profile=profile, preview=not no_browser)


@cli.command('create-database')
@click.argument('raster-pattern', type=RasterPattern(), required=True)
@click.option('-o', '--output-file', type=PathlibPath(dir_okay=False), required=True)
@click.option('--overwrite', is_flag=True, default=False)
@click.option('--skip-metadata', is_flag=True, default=False)
def create_database(raster_pattern, output_file, overwrite=False, skip_metadata=False):
    """Create a new raster database from a collection of raster files.

    This command only supports the creation of an SQLite database without any additional metadata.
    For more sophisticated use cases use the Python API.
    """
    import tqdm
    from terracotta import get_driver

    if output_file.is_file() and not overwrite:
        click.confirm(f'Output file {output_file} exists. Continue?', abort=True)

    keys, raster_files = raster_pattern
    driver = get_driver(output_file)
    pbar = tqdm.tqdm(raster_files.items())

    with driver.connect():
        driver.create(keys, drop_if_exists=True)
        for key, filepath in pbar:
            pbar.set_postfix({'file': filepath})
            driver.insert(key, filepath, compute_metadata=not skip_metadata)


@cli.command('optimize-rasters')
@click.argument('raster-files', nargs=-1, type=GlobbityGlob(), required=True)
@click.option('-o', '--output-folder', type=PathlibPath(file_okay=False), required=True)
@click.option('--overwrite', is_flag=True, default=False)
def optimize_rasters(raster_files, output_folder, overwrite=False):
    """Optimize a collection of raster files for use with Terracotta.

    Note that all rasters may only contain a single band. GDAL is required to run this command.

    For COG spec see https://trac.osgeo.org/gdal/wiki/CloudOptimizedGeoTIFF
    """
    import subprocess
    import shutil

    import tqdm

    output_folder.mkdir(exist_ok=True)

    raster_files = set(itertools.chain.from_iterable(raster_files))
    pbar = tqdm.tqdm(raster_files, desc='Optimizing raster files')

    def abort(msg):
        pbar.close()
        click.echo(msg)
        raise click.Abort()

    def call_gdal(cmd):
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as exc:
            abort(f'Error while running GDAL: {exc!s}')
        if 'ERROR' in output:
            error_lines = '\n'.join(line for line in output if 'ERROR' in line)
            abort(f'Error while running GDAL:\n{error_lines}')

    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = pathlib.Path(tempdir)
        for input_file in pbar:
            pbar.set_postfix({'file': str(input_file)})

            temp_output_file = tempdir / input_file.name
            call_gdal([
                'gdal_translate', str(input_file), str(temp_output_file), '-co', 'TILED=YES',
                '-co', 'COMPRESS=DEFLATE'
            ])
            call_gdal([
                'gdaladdo', '-r', 'nearest', str(temp_output_file), '2', '4', '8', '16', '32', '64'
            ])
            temp_output_file_co = tempdir / (input_file.stem + '_co' + input_file.suffix)
            temp_aux_file_co = tempdir / (temp_output_file_co.name + '.aux.xml')
            call_gdal([
                'gdal_translate', str(temp_output_file), str(temp_output_file_co),
                '-co', 'TILED=YES', '-co', 'COMPRESS=DEFLATE', '-co', 'PHOTOMETRIC=MINISBLACK',
                '-co', 'COPY_SRC_OVERVIEWS=YES', '-co', 'BLOCKXSIZE=256', '-co', 'BLOCKYSIZE=256',
                '--config', 'GDAL_TIFF_OVR_BLOCKSIZE', '256'
            ])

            output_file = output_folder / input_file.name
            if not overwrite and output_file.is_file():
                abort(f'Output file {output_file!s} exists (use --overwrite to ignore)')

            shutil.move(str(temp_output_file_co), output_file)

            if temp_aux_file_co.is_file():
                shutil.move(str(temp_aux_file_co), output_folder / (output_file.name + '.aux.xml'))
