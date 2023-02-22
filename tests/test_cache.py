import zlib

import numpy as np


def test_get_size():
    from terracotta.cache import CompressedLFUCache
    tile_shape = (256, 256)
    data = zlib.compress(np.ones(tile_shape), 9)
    mask = zlib.compress(np.zeros(tile_shape), 9)
    size = CompressedLFUCache._get_size((data, mask, 'float64', tile_shape))
    assert 1450 < size < 1550
