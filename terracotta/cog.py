"""cog.py

Provides a validator for cloud-optimized GeoTiff.
"""

from typing import Tuple, List, Dict, Any

import os

import rasterio
from rasterio.env import GDALVersion
from rasterio._base import DatasetBase

ValidationInfo = Tuple[List[str], List[str], Dict[str, Any]]


def validate(src_path: str, strict: bool = True) -> bool:
    """Validate given cloud-optimized GeoTIFF"""
    errors, warnings, details = check_raster_file(src_path)
    if strict:
        return not errors and not warnings
    else:
        return not errors


def is_tiled(src: DatasetBase) -> bool:
    """
    Check if a rasterio dataset is tiled.

    Implementation copied from
    https://github.com/rasterio/rasterio/blob/74ccaf126d08fc6eca3eacd7cb20ac8bb155ee3b/rasterio/_base.pyx#L1006-L1017
    Since this was deprecated in rasterio

    :param src: rasterio dataset
    """
    # It's rare but possible that a dataset's bands have different block structure.
    # Therefore we check them all against the width of the dataset.
    return src.block_shapes and all(src.width != w for _, w in src.block_shapes)


def check_raster_file(src_path: str) -> ValidationInfo:  # pragma: no cover
    """
    Implementation from
    https://github.com/cogeotiff/rio-cogeo/blob/a07d914e2d898878417638bbc089179f01eb5b28/rio_cogeo/cogeo.py#L385

    This function is the rasterio equivalent of
    https://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/validate_cloud_optimized_geotiff.py
    """
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}

    if not GDALVersion.runtime().at_least("2.2"):
        raise RuntimeError("GDAL 2.2 or above required")

    config = dict(GDAL_DISABLE_READDIR_ON_OPEN="FALSE")
    with rasterio.Env(**config):
        with rasterio.open(src_path) as src:
            if not src.driver == "GTiff":
                errors.append("The file is not a GeoTIFF")
                return errors, warnings, details

            if any(os.path.splitext(x)[-1] == ".ovr" for x in src.files):
                errors.append(
                    "Overviews found in external .ovr file. They should be internal"
                )

            overviews = src.overviews(1)
            if src.width > 512 and src.height > 512:
                if not is_tiled(src):
                    errors.append(
                        "The file is greater than 512xH or 512xW, but is not tiled"
                    )

                if not overviews:
                    warnings.append(
                        "The file is greater than 512xH or 512xW, it is recommended "
                        "to include internal overviews"
                    )

            ifd_offset = int(src.get_tag_item("IFD_OFFSET", "TIFF", bidx=1))
            # Starting from GDAL 3.1, GeoTIFF and COG have ghost headers
            # e.g:
            # """
            # GDAL_STRUCTURAL_METADATA_SIZE=000140 bytes
            # LAYOUT=IFDS_BEFORE_DATA
            # BLOCK_ORDER=ROW_MAJOR
            # BLOCK_LEADER=SIZE_AS_UINT4
            # BLOCK_TRAILER=LAST_4_BYTES_REPEATED
            # KNOWN_INCOMPATIBLE_EDITION=NO
            # """
            #
            # This header should be < 200bytes
            if ifd_offset > 300:
                errors.append(
                    f"The offset of the main IFD should be < 300. It is {ifd_offset} instead"
                )

            ifd_offsets = [ifd_offset]
            details["ifd_offsets"] = {}
            details["ifd_offsets"]["main"] = ifd_offset

            if overviews and overviews != sorted(overviews):
                errors.append("Overviews should be sorted")

            for ix, dec in enumerate(overviews):

                # NOTE: Size check is handled in rasterio `src.overviews` methods
                # https://github.com/mapbox/rasterio/blob/4ebdaa08cdcc65b141ed3fe95cf8bbdd9117bc0b/rasterio/_base.pyx
                # We just need to make sure the decimation level is > 1
                if not dec > 1:
                    errors.append(
                        "Invalid Decimation {} for overview level {}".format(dec, ix)
                    )

                # Check that the IFD of descending overviews are sorted by increasing
                # offsets
                ifd_offset = int(src.get_tag_item("IFD_OFFSET", "TIFF", bidx=1, ovr=ix))
                ifd_offsets.append(ifd_offset)

                details["ifd_offsets"]["overview_{}".format(ix)] = ifd_offset
                if ifd_offsets[-1] < ifd_offsets[-2]:
                    if ix == 0:
                        errors.append(
                            "The offset of the IFD for overview of index {} is {}, "
                            "whereas it should be greater than the one of the main "
                            "image, which is at byte {}".format(
                                ix, ifd_offsets[-1], ifd_offsets[-2]
                            )
                        )
                    else:
                        errors.append(
                            "The offset of the IFD for overview of index {} is {}, "
                            "whereas it should be greater than the one of index {}, "
                            "which is at byte {}".format(
                                ix, ifd_offsets[-1], ix - 1, ifd_offsets[-2]
                            )
                        )

            block_offset = src.get_tag_item("BLOCK_OFFSET_0_0", "TIFF", bidx=1)

            data_offset = int(block_offset) if block_offset else 0
            data_offsets = [data_offset]
            details["data_offsets"] = {}
            details["data_offsets"]["main"] = data_offset

            for ix, dec in enumerate(overviews):
                block_offset = src.get_tag_item(
                    "BLOCK_OFFSET_0_0", "TIFF", bidx=1, ovr=ix
                )
                data_offset = int(block_offset) if block_offset else 0
                data_offsets.append(data_offset)
                details["data_offsets"]["overview_{}".format(ix)] = data_offset

            if data_offsets[-1] != 0 and data_offsets[-1] < ifd_offsets[-1]:
                if len(overviews) > 0:
                    errors.append(
                        "The offset of the first block of the smallest overview "
                        "should be after its IFD"
                    )
                else:
                    errors.append(
                        "The offset of the first block of the image should "
                        "be after its IFD"
                    )

            for i in range(len(data_offsets) - 2, 0, -1):
                if data_offsets[i] < data_offsets[i + 1]:
                    errors.append(
                        "The offset of the first block of overview of index {} should "
                        "be after the one of the overview of index {}".format(i - 1, i)
                    )

            if len(data_offsets) >= 2 and data_offsets[0] < data_offsets[1]:
                errors.append(
                    "The offset of the first block of the main resolution image "
                    "should be after the one of the overview of index {}".format(
                        len(overviews) - 1
                    )
                )

        for ix, dec in enumerate(overviews):
            with rasterio.open(src_path, OVERVIEW_LEVEL=ix) as ovr_dst:
                if ovr_dst.width > 512 and ovr_dst.height > 512:
                    if not is_tiled(ovr_dst):
                        errors.append("Overview of index {} is not tiled".format(ix))

    return errors, warnings, details
