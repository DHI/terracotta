import os
import json
import functools

from flask import (Flask, Blueprint, current_app, abort, send_file, jsonify, request,
                   render_template)

from terracotta import exceptions

flask_api = Blueprint('flask_api', __name__)


def convert_exceptions(fun):

    @functools.wraps(fun)
    def inner(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except (exceptions.DatasetNotFoundError, exceptions.UnknownKeyError):
            if current_app.debug:
                raise
            abort(404)
        except (exceptions.InvalidArgumentsError, exceptions.TileOutOfBoundsError):
            if current_app.debug:
                raise
            abort(400)

    return inner


@flask_api.route('/rgb/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@convert_exceptions
def get_rgb(tile_z, tile_y, tile_x, path):
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.rgb import rgb

    some_keys = path.split('/')

    tile_xyz = (tile_x, tile_y, tile_z)
    rgb_values = [request.args.get(k) for k in ('r', 'g', 'b')]

    if not all(rgb_values):
        raise exceptions.InvalidArgumentsError('r, g, and b arguments must be given')

    stretch_method = request.args.get('stretch_method', 'stretch')
    stretch_options = {
        'data_range': [json.loads(request.args.get(k, 'null')) for k in
                       ('r_range', 'g_range', 'b_range')],
        'percentiles': json.loads(request.args.get('percentiles', 'null'))
    }

    image = rgb(
        some_keys, tile_xyz, rgb_values,
        stretch_method=stretch_method, stretch_options=stretch_options
    )

    return send_file(image, mimetype='image/png')


@flask_api.route('/singleband/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                 methods=['GET'])
@convert_exceptions
def get_singleband(tile_z, tile_y, tile_x, path):
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.singleband import singleband

    keys = path.split('/')

    tile_xyz = (tile_x, tile_y, tile_z)

    stretch_method = request.args.get('stretch_method', 'stretch')
    stretch_options = {k: json.loads(request.args[k]) for k in ('data_range', 'percentiles')
                       if k in request.args}
    colormap = request.args.get('colormap', 'inferno')

    image = singleband(
        keys, tile_xyz, colormap=colormap,
        stretch_method=stretch_method, stretch_options=stretch_options
    )

    return send_file(image, mimetype='image/png')


@flask_api.route('/datasets', methods=['GET'])
@convert_exceptions
def get_datasets():
    """Send back all available key combinations"""
    from terracotta.handlers.datasets import datasets
    keys = dict(request.args.items()) or None
    available_datasets = datasets(keys)
    return jsonify(available_datasets)


@flask_api.route('/metadata/<path:path>', methods=['GET'])
@convert_exceptions
def get_metadata(path):
    """Send back dataset metadata as json"""
    from terracotta.handlers.metadata import metadata
    keys = path.split('/')
    meta = metadata(keys)
    return jsonify(meta)


@flask_api.route('/keys', methods=['GET'])
@convert_exceptions
def get_keys():
    """Send back a JSON list of all key names"""
    from terracotta.handlers.keys import keys
    return jsonify(keys())


@flask_api.route('/colormaps', methods=['GET'])
@convert_exceptions
def get_cmaps():
    """Send back a JSON list of all registered colormaps"""
    from terracotta.handlers.colormaps import colormaps
    return jsonify(colormaps())


@flask_api.route('/', methods=['GET'])
def get_map():
    return render_template('map.html')


def create_app(debug=False, profile=False):
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.register_blueprint(flask_api, url_prefix='')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.config['PROFILE'] = True
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    return new_app


def run_app(*args, allow_all_ips=False, port=None, preview=False, **kwargs):
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    port = 5000
    host = '0.0.0.0' if allow_all_ips else 'localhost'
    if preview and 'WERKZEUG_RUN_MAIN' not in os.environ:
        import threading
        import webbrowser
        threading.Timer(2, lambda: webbrowser.open(f'http://127.0.0.1:{port}/')).start()

    app.run(host=host, port=port, threaded=True)
