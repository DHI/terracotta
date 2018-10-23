"""cog.py

Provides a validator for cloud-optimized GeoTiff.

Implementation from
https://github.com/mapbox/rio-cogeo/blob/eefb3487002042114876e49ce1f86da9c6cef30a/rio_cogeo/cogeo.py

This script is the rasterio equivalent of
https://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/validate_cloud_optimized_geotiff.py
"""

import os

import rasterio
from rasterio.env import GDALVersion


def validate(src_path: str) -> bool:
    """Validate given cloud-optimized GeoTIFF"""

    if not GDALVersion.runtime().at_least('2.2'):
        raise RuntimeError('GDAL 2.2 or above required')

    with rasterio.open(src_path) as src:
        if not src.driver == 'GTiff':
            # Not a GeoTIFF
            return False

        filelist = [os.path.basename(f) for f in src.files]
        src_bname = os.path.basename(src_path)
        if len(filelist) > 1 and src_bname + '.ovr' in filelist:
            # Overviews found in external .ovr file. They should be internal
            return False

        overviews = src.overviews(1) or []

        if src.width >= 512 or src.height >= 512:
            if not src.is_tiled:
                # The file is greater than 512xH or 512xW, but is not tiled
                return False

            if not overviews:
                # The file is greater than 512xH or 512xW, but has no overviews
                return False

        ifd_offset = int(src.get_tag_item('IFD_OFFSET', 'TIFF', bidx=1))
        ifd_offsets = [ifd_offset]
        if ifd_offset not in (8, 16):
            # The offset of the main IFD should be 8 for ClassicTIFF or 16 for BigTIFF
            return False

        if not overviews == sorted(overviews):
            # Overviews should be sorted
            return False

        for ix, dec in enumerate(overviews):
            if not dec > 1:
                # Invalid Decimation
                return False

            # TODO: Check if the overviews are tiled
            # NOTE: There is currently no way to do that with rasterio

            # Check that the IFD of descending overviews are sorted by increasing offsets
            ifd_offset = int(src.get_tag_item('IFD_OFFSET', 'TIFF', bidx=1, ovr=ix))
            ifd_offsets.append(ifd_offset)

            if ifd_offsets[-1] < ifd_offsets[-2]:
                return False

        block_offset = int(src.get_tag_item('BLOCK_OFFSET_0_0', 'TIFF', bidx=1))
        if not block_offset:
            return False

        data_offset = int(block_offset)
        data_offsets = [data_offset]

        for ix, dec in enumerate(overviews):
            data_offset = int(
                src.get_tag_item('BLOCK_OFFSET_0_0', 'TIFF', bidx=1, ovr=ix)
            )
            data_offsets.append(data_offset)

        if data_offsets[-1] < ifd_offsets[-1]:
            return False

        for i in range(len(data_offsets) - 2, 0, -1):
            if data_offsets[i] < data_offsets[i + 1]:
                return False

        if len(data_offsets) >= 2 and data_offsets[0] < data_offsets[1]:
            return False

    return True
