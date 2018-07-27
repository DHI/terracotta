"""scripts/optimize_rasters.py

Convert some raster files to cloud-optimized GeoTiff for use with Terracotta.
"""

from typing import Sequence, List
import os
import subprocess
import shutil
import itertools
import tempfile
from pathlib import Path

import click

from terracotta.scripts.click_utils import GlobbityGlob, PathlibPath


@click.command('optimize-rasters',
               short_help='Optimize a collection of raster files for use with Terracotta.')
@click.argument('raster-files', nargs=-1, type=GlobbityGlob(), required=True)
@click.option('-o', '--output-folder', type=PathlibPath(file_okay=False), required=True,
              help='Output folder for cloud-optimized rasters. Subdirectories will be flattened.')
@click.option('--overwrite', is_flag=True, default=False,
              help='Force overwrite of existing files')
def optimize_rasters(raster_files: Sequence[Sequence[Path]],
                     output_folder: Path,
                     overwrite: bool = False) -> None:
    """Optimize a collection of raster files for use with Terracotta.

    First argument is a list of input files or glob patterns.

    Example:

        terracotta optimize-rasters rasters/*.tif -o cloud-optimized/

    Note that all rasters may only contain a single band. GDAL is required to run this command.

    For COG spec see https://trac.osgeo.org/gdal/wiki/CloudOptimizedGeoTIFF
    """
    try:
        import tqdm
        has_tqdm = True
    except ImportError:
        has_tqdm = False

    raster_files_flat = sorted(set(itertools.chain.from_iterable(raster_files)))

    for f in raster_files_flat:
        if not f.is_file():
            raise ValueError(f'Input file {f!s} is not a file')

    output_folder.mkdir(exist_ok=True)

    os.environ['GDAL_NUM_THREADS'] = 'ALL_CPUS'

    if has_tqdm:
        pbar = tqdm.tqdm(raster_files_flat, desc='Optimizing raster files')
    else:
        pbar = raster_files_flat

    def call_gdal(cmd: List[str]) -> None:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as exc:
            pbar.close()
            output = exc.output.decode('utf-8')
            error_lines = '\n'.join(['Error while running GDAL:', str(exc), output])
            raise RuntimeError(error_lines) from exc
        if 'ERROR' in output:
            pbar.close()
            error_lines = '\n'.join(line for line in output.split('\n') if 'ERROR' in line)
            raise RuntimeError(f'Error while running GDAL:\n{error_lines}')

    with tempfile.TemporaryDirectory() as t:
        tempdir = Path(t)
        for input_file in pbar:
            if has_tqdm:
                pbar.set_postfix({'file': input_file.name})
            else:
                click.echo(input_file.name)

            output_file = output_folder / input_file.with_suffix('.tif').name
            if not overwrite and output_file.is_file():
                raise click.UsageError(f'Output file {output_file!s} exists '
                                       '(use --overwrite to ignore)')

            temp_output_file = tempdir / f'{input_file.stem}.tif'
            call_gdal([
                'gdal_translate', str(input_file), str(temp_output_file), '-co', 'TILED=YES',
                '-co', 'COMPRESS=DEFLATE'
            ])
            call_gdal([
                'gdaladdo', '-r', 'average', str(temp_output_file), '2', '4', '8', '16', '32', '64'
            ])
            temp_output_file_co = temp_output_file.with_name(f'{input_file.stem}_co.tif')
            temp_aux_file_co = temp_output_file_co.with_suffix('.tif.aux.xml')
            call_gdal([
                'gdal_translate', str(temp_output_file), str(temp_output_file_co),
                '-co', 'TILED=YES', '-co', 'COMPRESS=DEFLATE', '-co', 'PHOTOMETRIC=MINISBLACK',
                '-co', 'COPY_SRC_OVERVIEWS=YES', '-co', 'BLOCKXSIZE=256', '-co', 'BLOCKYSIZE=256',
                '--config', 'GDAL_TIFF_OVR_BLOCKSIZE', '256'
            ])

            shutil.move(str(temp_output_file_co), output_file)

            if temp_aux_file_co.is_file():
                shutil.move(str(temp_aux_file_co), output_file.with_suffix('.tif.aux.xml'))
