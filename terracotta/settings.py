import os

CACHE_SIZE = int(os.environ.get('TC_CACHE_SIZE', 1024 * 1024 * 500))
TILE_SIZE = (int(os.environ.get('TC_TILE_SIZE', 256)), int(os.environ.get('TC_TILE_SIZE', 256)))
