"""cache.py

Custom cache implementations.
"""

from typing import Tuple, Callable, Any

import sys
import zlib

import numpy as np
from cachetools import LFUCache

CompressionTuple = Tuple[bytes, bytes, str, Tuple[int, int]]
SizeFunction = Callable[[CompressionTuple], int]


class CompressedLFUCache(LFUCache):
    """Least-frequently-used cache with ZLIB compression"""

    def __init__(self, maxsize: int, compression_level: int):
        super().__init__(maxsize, self._get_size)
        self.compression_level = compression_level

    def __getitem__(self, key: Any) -> np.ma.MaskedArray:
        compressed_item = super().__getitem__(key)
        return self._decompress_tuple(compressed_item)

    def __setitem__(self, key: Any,
                    value: np.ma.MaskedArray) -> None:
        val_compressed = self._compress_ma(value, self.compression_level)
        super().__setitem__(key, val_compressed)

    @staticmethod
    def _compress_ma(arr: np.ma.MaskedArray, compression_level: int) -> CompressionTuple:
        compressed_data = zlib.compress(arr.data, compression_level)
        mask_to_int = np.packbits(arr.mask.astype(np.uint8))
        compressed_mask = zlib.compress(mask_to_int, compression_level)
        out = (
            compressed_data,
            compressed_mask,
            arr.dtype.name,
            arr.shape
        )
        return out

    @staticmethod
    def _decompress_tuple(compressed_data: CompressionTuple) -> np.ma.MaskedArray:
        data_b, mask_b, dt, ds = compressed_data
        data = np.frombuffer(zlib.decompress(data_b), dtype=dt).reshape(ds)
        mask = np.frombuffer(zlib.decompress(mask_b), dtype=np.uint8)
        mask = np.unpackbits(mask)[:int(np.prod(ds))]
        mask = mask.reshape(ds)
        return np.ma.masked_array(data, mask=mask)

    @staticmethod
    def _get_size(x: Tuple) -> int:
        sizes = map(sys.getsizeof, x)
        return sum(sizes)
