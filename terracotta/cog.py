"""cog.py

Provides a validator for cloud-optimized GeoTiff.
"""

from typing import Tuple, List, Dict, Any

import os

import rasterio
from rasterio.env import GDALVersion

ValidationInfo = Tuple[List[str], List[str], Dict[str, Any]]


def validate(src_path: str, strict: bool = True) -> bool:
    """Validate given cloud-optimized GeoTIFF"""
    errors, warnings, details = check_raster_file(src_path)
    if strict:
        return not errors and not warnings
    else:
        return not errors


def check_raster_file(src_path: str) -> ValidationInfo:  # pragma: no cover
    """
    Implementation from
    https://github.com/cogeotiff/rio-cogeo/blob/0f00a6ee1eff602014fbc88178a069bd9f4a10da/rio_cogeo/cogeo.py

    This function is the rasterio equivalent of
    https://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/validate_cloud_optimized_geotiff.py
    """
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}

    if not GDALVersion.runtime().at_least('2.2'):
        raise RuntimeError('GDAL 2.2 or above required')

    config = dict(GDAL_DISABLE_READDIR_ON_OPEN='FALSE')
    with rasterio.Env(**config):
        with rasterio.open(src_path) as src:
            if not src.driver == 'GTiff':
                errors.append('The file is not a GeoTIFF')
                return errors, warnings, details

            filelist = [os.path.basename(f) for f in src.files]
            src_bname = os.path.basename(src_path)
            if len(filelist) > 1 and src_bname + '.ovr' in filelist:
                errors.append(
                    'Overviews found in external .ovr file. They should be internal'
                )

            overviews = src.overviews(1)
            if src.width >= 512 or src.height >= 512:
                if not src.is_tiled:
                    errors.append(
                        'The file is greater than 512xH or 512xW, but is not tiled'
                    )

                if not overviews:
                    warnings.append(
                        'The file is greater than 512xH or 512xW, it is recommended '
                        'to include internal overviews'
                    )

            ifd_offset = int(src.get_tag_item('IFD_OFFSET', 'TIFF', bidx=1))
            ifd_offsets = [ifd_offset]
            if ifd_offset > 300:
                errors.append(
                    f'The offset of the main IFD should be < 300. It is {ifd_offset} instead'
                )

            details['ifd_offsets'] = {}
            details['ifd_offsets']['main'] = ifd_offset

            if not overviews == sorted(overviews):
                errors.append('Overviews should be sorted')

            for ix, dec in enumerate(overviews):

                # NOTE: Size check is handled in rasterio `src.overviews` methods
                # https://github.com/mapbox/rasterio/blob/4ebdaa08cdcc65b141ed3fe95cf8bbdd9117bc0b/rasterio/_base.pyx
                # We just need to make sure the decimation level is > 1
                if not dec > 1:
                    errors.append(
                        'Invalid Decimation {} for overview level {}'.format(dec, ix)
                    )

                # Check that the IFD of descending overviews are sorted by increasing
                # offsets
                ifd_offset = int(src.get_tag_item('IFD_OFFSET', 'TIFF', bidx=1, ovr=ix))
                ifd_offsets.append(ifd_offset)

                details['ifd_offsets']['overview_{}'.format(ix)] = ifd_offset
                if ifd_offsets[-1] < ifd_offsets[-2]:
                    if ix == 0:
                        errors.append(
                            'The offset of the IFD for overview of index {} is {}, '
                            'whereas it should be greater than the one of the main '
                            'image, which is at byte {}'.format(
                                ix, ifd_offsets[-1], ifd_offsets[-2]
                            )
                        )
                    else:
                        errors.append(
                            'The offset of the IFD for overview of index {} is {}, '
                            'whereas it should be greater than the one of index {}, '
                            'which is at byte {}'.format(
                                ix, ifd_offsets[-1], ix - 1, ifd_offsets[-2]
                            )
                        )

            block_offset = int(src.get_tag_item('BLOCK_OFFSET_0_0', 'TIFF', bidx=1))
            if not block_offset:
                errors.append('Missing BLOCK_OFFSET_0_0')

            data_offset = int(block_offset) if block_offset else 0
            data_offsets = [data_offset]
            details['data_offsets'] = {}
            details['data_offsets']['main'] = data_offset

            for ix, dec in enumerate(overviews):
                data_offset = int(
                    src.get_tag_item('BLOCK_OFFSET_0_0', 'TIFF', bidx=1, ovr=ix)
                )
                data_offsets.append(data_offset)
                details['data_offsets']['overview_{}'.format(ix)] = data_offset

            if data_offsets[-1] < ifd_offsets[-1]:
                if len(overviews) > 0:
                    errors.append(
                        'The offset of the first block of the smallest overview '
                        'should be after its IFD'
                    )
                else:
                    errors.append(
                        'The offset of the first block of the image should '
                        'be after its IFD'
                    )

            for i in range(len(data_offsets) - 2, 0, -1):
                if data_offsets[i] < data_offsets[i + 1]:
                    errors.append(
                        'The offset of the first block of overview of index {} should '
                        'be after the one of the overview of index {}'.format(i - 1, i)
                    )

            if len(data_offsets) >= 2 and data_offsets[0] < data_offsets[1]:
                errors.append(
                    'The offset of the first block of the main resolution image '
                    'should be after the one of the overview of index {}'.format(
                        len(overviews) - 1
                    )
                )

        for ix, dec in enumerate(overviews):
            with rasterio.open(src_path, OVERVIEW_LEVEL=ix) as ovr_dst:
                if ovr_dst.width >= 512 or ovr_dst.height >= 512:
                    if not ovr_dst.is_tiled:
                        errors.append('Overview of index {} is not tiled'.format(ix))

    return errors, warnings, details
