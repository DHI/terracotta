import os
import threading
import webbrowser
import json

from flask import Flask, Blueprint, current_app, abort, send_file, jsonify, request, render_template

from terracotta.exceptions import TileNotFoundError, TileOutOfBoundsError, DatasetNotFoundError
# TODO: proper exception handling

flask_api = Blueprint('flask_api', __name__)


@flask_api.route('/rgb/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
def get_rgb(tile_z, tile_y, tile_x, path):
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.rgb import rgb

    driver = current_app.config['DRIVER']
    some_keys = path.split('/')
    if len(some_keys) != len(driver.available_keys) - 1:
        abort(404)
    tile_xyz = (tile_x, tile_y, tile_z)
    rgb_values = [request.args.get(k) for k in ('r', 'g', 'b')]
    if not all(rgb_values.values()):
        abort(400)
    stretch_method = request.args.get('stretch_method', 'stretch')
    stretch_options = {k: json.loads(request.args[k]) for k in ('data_range', 'percentiles')
                       if k in request.args}
    try:
        image = rgb(
            driver, some_keys, tile_xyz, rgb_values,
            stretch_method=stretch_method, stretch_options=stretch_options
        )
    except TileNotFoundError:
        abort(404)
    return send_file(image, mimetype='image/png')


@flask_api.route('/singleband/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                 methods=['GET'])
def get_singleband(tile_z, tile_y, tile_x, path):
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.singleband import singleband

    driver = current_app.config['DRIVER']
    keys = path.split('/')
    if len(keys) != len(driver.available_keys):
        abort(404)
    tile_xyz = (tile_x, tile_y, tile_z)

    stretch_method = request.args.get('stretch_method', 'stretch')
    stretch_options = {k: json.loads(request.args[k]) for k in ('data_range', 'percentiles')
                       if k in request.args}
    colormap = request.args.get('colormap', 'inferno')

    try:
        image = singleband(
            driver, keys, tile_xyz, colormap=colormap,
            stretch_method=stretch_method, stretch_options=stretch_options
        )
    except TileNotFoundError:
        abort(404)
    return send_file(image, mimetype='image/png')


@flask_api.route('/datasets', methods=['GET'])
def get_datasets():
    """Send back all available key combinations"""
    from terracotta.handlers.datasets import datasets
    driver = current_app.config['DRIVER']
    keys = dict(request.args.items()) or None
    print(keys)
    available_datasets = datasets(driver, keys)
    return jsonify(available_datasets)


@flask_api.route('/metadata/<path:path>', methods=['GET'])
def get_metadata(path):
    """Send back dataset metadata as json"""
    from terracotta.handlers.metadata import metadata
    driver = current_app.config['DRIVER']
    keys = path.split('/')
    if len(keys) != len(driver.available_keys):
        abort(404)

    try:
        meta = metadata(driver, keys)
    except DatasetNotFoundError:
        if current_app.debug:
            raise
        abort(404)

    return jsonify(meta)


@flask_api.route('/keys', methods=['GET'])
def get_keys():
    """Send back a JSON list of all key names"""
    from terracotta.handlers.keys import keys
    driver = current_app.config['DRIVER']
    return jsonify(keys(driver))


@flask_api.route('/colormaps', methods=['GET'])
def get_cmaps():
    """Send back a JSON list of all registered colormaps"""
    from terracotta.handlers.colormaps import colormaps
    return jsonify(colormaps())


@flask_api.route('/', methods=['GET'])
def get_map():
    return render_template('map.html')


def create_app(driver, debug=False, profile=False):
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.config['DRIVER'] = driver
    new_app.register_blueprint(flask_api, url_prefix='')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.config['PROFILE'] = True
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    return new_app


def run_app(*args, preview=False, **kwargs):
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    port = 5000
    if preview and 'WERKZEUG_RUN_MAIN' not in os.environ:
        threading.Timer(2, lambda: webbrowser.open('http://127.0.0.1:%d/' % port)).start()

    app.run(port=port)
