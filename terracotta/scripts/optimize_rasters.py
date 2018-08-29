"""scripts/optimize_rasters.py

Convert some raster files to cloud-optimized GeoTiff for use with Terracotta.
"""

from typing import Sequence
import itertools
from pathlib import Path

import click

from terracotta.scripts.click_utils import GlobbityGlob, PathlibPath

OVERVIEW_LEVEL = 6
GDAL_CONFIG = {
    'GDAL_NUM_THREADS': 'ALL_CPUS',
    'GDAL_TIFF_INTERNAL_MASK': True,
    'GDAL_TIFF_OVR_BLOCKSIZE': 256,
}
COG_PROFILE = {
    'count': 1,
    'driver': 'GTiff',
    'interleave': 'pixel',
    'tiled': True,
    'blockxsize': 256,
    'blockysize': 256,
    'compress': 'DEFLATE',
    'photometric': 'MINISBLACK',
    'BIGTIFF': 'IF_SAFER'
}


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

    Note that all rasters may only contain a single band.
    """
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.enums import Resampling
    from rasterio.shutil import copy

    raster_files_flat = sorted(set(itertools.chain.from_iterable(raster_files)))

    if not raster_files_flat:
        click.echo('No files given')
        return

    for f in raster_files_flat:
        if not f.is_file():
            raise click.Abort(f'Input raster {f!s} is not a file')

    output_folder.mkdir(exist_ok=True)

    pbar_args = dict(
        label='Optimizing raster files',
        show_eta=False,
        item_show_func=lambda s: s.name if s else ''
    )

    click.echo('')
    with click.progressbar(raster_files_flat, **pbar_args) as pbar:  # type: ignore
        for input_file in pbar:
            output_file = output_folder / input_file.with_suffix('.tif').name

            if not overwrite and output_file.is_file():
                raise click.Abort(f'Output file {output_file!s} exists (use --overwrite to ignore)')

            with rasterio.Env(**GDAL_CONFIG), rasterio.open(str(input_file)) as src:
                profile = src.profile.copy()
                profile.update(COG_PROFILE)

                with MemoryFile() as memfile, memfile.open(**profile) as mem:
                    mask = np.zeros((mem.height, mem.width), dtype=np.uint8)
                    windows = list(mem.block_windows(1))

                    for _, w in windows:
                        block_data = src.read(window=w, indexes=[1])
                        mem.write(block_data, window=w)
                        mask_value = src.dataset_mask(window=w)

                        mask[w.row_off:w.row_off + w.height,
                             w.col_off:w.col_off + w.width] = mask_value

                    mem.write_mask(mask)

                    overviews = [2 ** j for j in range(1, OVERVIEW_LEVEL + 1)]
                    mem.build_overviews(overviews, Resampling.average)
                    mem.update_tags(ns='tc_overview', resampling=Resampling.average.value)

                    copy(mem, str(output_file), copy_src_overviews=True, **COG_PROFILE)
