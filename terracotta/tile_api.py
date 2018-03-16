from io import BytesIO

from flask import Blueprint, current_app, abort, send_file, jsonify
import numpy as np
from cachetools import LFUCache, cached

import terracotta.tile as tile
from terracotta.tile import TileNotFoundError, TileOutOfBoundsError, DatasetNotFoundError
import terracotta.encode_decode as ed


DEFAULT_CACHE_SIZE = 1000000000  # 1GB


tile_api = Blueprint('tile_api', __name__)
cache = None
tilestore = None


def init(datasets, cache_size=DEFAULT_CACHE_SIZE):
    global cache
    global tilestore
    cache = LFUCache(cache_size)
    tilestore = tile.TileStore(datasets)


@tile_api.route('/<dataset>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@tile_api.route('/<dataset>/<timestep>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
@cached(cache)
def get_tile(dataset, tile_z, tile_x, tile_y, timestep=None):
    """Respond to tile requests"""

    try:
        img, alpha_mask = tilestore.tile(tile_x, tile_y, tile_z, dataset, timestep)
    except TileNotFoundError:
        if current_app.debug:
            raise
        abort(404)
    except TileOutOfBoundsError:
        nodata = tilestore.get_nodata(dataset)
        img = np.full((256, 256), nodata, dtype=np.uint8)
        alpha_mask = np.zeros((256, 256), dtype=np.uint8)

    range = tilestore.get_meta(dataset)['range']
    # img = ed.contrast_stretch(img, range)
    img = ed.img_cmap(img, range)
    img = ed.array_to_img(img, alpha_mask=alpha_mask)

    sio = BytesIO()
    img.save(sio, 'png', compress_level=0)
    sio.seek(0)

    return send_file(sio, mimetype='image/png')


@tile_api.route('/datasets', methods=['GET'])
def get_datasets():
    """Send back names of available datasets"""
    datasets = list(tilestore.get_datasets())

    return jsonify({'datasets': datasets})


@tile_api.route('/meta/<dataset>', methods=['GET'])
def get_meta(dataset):
    """Send back dataset metadata as json"""
    try:
        meta = tilestore.get_meta(dataset)
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    return jsonify(meta)


@tile_api.route('/timesteps/<dataset>', methods=['GET'])
def get_timesteps(dataset):
    """Send back list of timesteps for dataset as json."""
    try:
        timesteps = sorted(tilestore.get_timesteps(dataset))
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    return jsonify(timesteps)


@tile_api.route('/bounds/<dataset>', methods=['GET'])
def get_bounds(dataset):
    """Send back WGS bounds of dataset"""
    try:
        bounds = tilestore.get_bounds(dataset)
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    return jsonify(bounds)
