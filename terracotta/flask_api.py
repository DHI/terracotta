from io import BytesIO

from flask import Blueprint, current_app, abort, send_file, jsonify, render_template
import numpy as np
import matplotlib
import matplotlib.cm as cm

import terracotta.tile as tile
from terracotta.tile import TileNotFoundError, TileOutOfBoundsError, DatasetNotFoundError
import terracotta.encode_decode as ed


flask_api = Blueprint('flask_api', __name__)
tilestore = None


def init(**kwargs):
    global tilestore
    tilestore = tile.TileStore(**kwargs)


@flask_api.route('/tile/<dataset>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@flask_api.route('/tile/<dataset>/<timestep>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                methods=['GET'])
def get_tile(dataset, tile_z, tile_x, tile_y, timestep=None):
    """Respond to tile requests"""

    try:
        img, alpha_mask = tilestore.tile(dataset, tile_x, tile_y, tile_z, timestep)
    except (TileNotFoundError, DatasetNotFoundError):
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


@flask_api.route('/datasets', methods=['GET'])
def get_datasets():
    """Send back names of available datasets"""
    datasets = list(tilestore.get_datasets())

    return jsonify({'datasets': datasets})


@flask_api.route('/meta/<dataset>', methods=['GET'])
def get_meta(dataset):
    """Send back dataset metadata as json"""
    try:
        meta = tilestore.get_meta(dataset)
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    return jsonify(meta)


@flask_api.route('/timesteps/<dataset>', methods=['GET'])
def get_timesteps(dataset):
    """Send back list of timesteps for dataset as json."""
    try:
        timesteps = tilestore.get_timesteps(dataset)
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    return jsonify({'timesteps': timesteps})


@flask_api.route('/bounds/<dataset>', methods=['GET'])
def get_bounds(dataset):
    """Send back WGS bounds of dataset"""
    try:
        bounds = tilestore.get_bounds(dataset)
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    return jsonify(bounds)


@tile_api.route('/', methods=['GET'])
def get_map():
    if not current_app.debug:
        abort(404)
    return render_template('map.html')


@flask_api.route('/legend/<dataset>', methods=['GET'])
def get_legend(dataset):
    """Send back JSON of class names or min/max
    with corresponding color as hex"""
    try:
        classes = tilestore.get_classes(dataset)
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    val_range = tilestore.get_meta(dataset)['range']
    names, vals = zip(*classes.items())

    # Cmapper
    normalizer = matplotlib.colors.Normalize(vmin=val_range[0], vmax=val_range[1], clip=True)
    mapper = cm.ScalarMappable(norm=normalizer, cmap='inferno')

    rgbs = [mapper.to_rgba(x, bytes=True) for x in vals]
    hex = ['#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2]) for rgb in rgbs]

    names_hex = dict(zip(names, hex))
    legend = {'legend': names_hex}

    return jsonify(legend)
