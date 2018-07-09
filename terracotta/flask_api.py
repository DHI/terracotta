from typing import Callable, Any
import os
import json
import functools

from flask import (Flask, Blueprint, current_app, abort, send_file, jsonify, request,
                   render_template)

from terracotta import exceptions

flask_api = Blueprint('flask_api', __name__)


def convert_exceptions(fun: Callable) -> Callable:
    """Converts internal exceptions to appropriate HTTP responses"""

    @functools.wraps(fun)
    def inner(*args: Any, **kwargs: Any) -> Any:
        try:
            return fun(*args, **kwargs)

        except exceptions.TileOutOfBoundsError:
            # send empty image
            from terracotta import get_settings, image
            settings = get_settings()
            return send_file(image.empty_image(settings.TILE_SIZE), mimetype='image/png')

        except (exceptions.DatasetNotFoundError, exceptions.UnknownKeyError):
            # wrong path -> 404
            if current_app.debug:
                raise
            abort(404)

        except exceptions.InvalidArgumentsError:
            # wrong query arguments -> 400
            if current_app.debug:
                raise
            abort(400)

    return inner


@flask_api.route('/rgb/<int:tile_z>/<int:tile_x>/<int:tile_y>.png')
@flask_api.route('/rgb/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png', methods=['GET'])
@convert_exceptions
def get_rgb(tile_z: int, tile_y: int, tile_x: int, path: str = '') -> Any:
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.rgb import rgb

    some_keys = [key for key in path.split('/') if key]

    tile_xyz = (tile_x, tile_y, tile_z)
    rgb_values = [request.args.get(k) for k in ('r', 'g', 'b')]

    if not all(rgb_values):
        raise exceptions.InvalidArgumentsError('r, g, and b arguments must be given')

    stretch_ranges = [json.loads(request.args.get(f'{k}_range', 'null')) for k in ('r', 'g', 'b')]

    image = rgb(
        some_keys, tile_xyz, rgb_values, stretch_ranges=stretch_ranges
    )

    return send_file(image, mimetype='image/png')


@flask_api.route('/singleband/<path:path>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png',
                 methods=['GET'])
@convert_exceptions
def get_singleband(tile_z: int, tile_y: int, tile_x: int, path: str) -> Any:
    """Return PNG image of requested RGB tile"""
    from terracotta.handlers.singleband import singleband

    keys = [key for key in path.split('/') if key]

    tile_xyz = (tile_x, tile_y, tile_z)

    stretch_range = json.loads(request.args.get('stretch_range', 'null'))
    colormap = request.args.get('colormap')

    image = singleband(
        keys, tile_xyz, colormap=colormap, stretch_range=stretch_range
    )

    return send_file(image, mimetype='image/png')


@flask_api.route('/datasets', methods=['GET'])
@convert_exceptions
def get_datasets() -> str:
    """Send back all available key combinations"""
    from terracotta.handlers.datasets import datasets
    keys = dict(request.args.items()) or None
    available_datasets = datasets(keys)
    return jsonify(available_datasets)


@flask_api.route('/metadata/<path:path>', methods=['GET'])
@convert_exceptions
def get_metadata(path: str) -> str:
    """Send back dataset metadata as json"""
    from terracotta.handlers.metadata import metadata
    keys = [key for key in path.split('/') if key]
    meta = metadata(keys)
    return jsonify(meta)


@flask_api.route('/keys', methods=['GET'])
@convert_exceptions
def get_keys() -> str:
    """Send back a JSON list of all key names"""
    from terracotta.handlers.keys import keys
    return jsonify(keys())


@flask_api.route('/colormaps', methods=['GET'])
@convert_exceptions
def get_cmaps() -> str:
    """Send back a JSON list of all registered colormaps"""
    from terracotta.handlers.colormaps import colormaps
    return jsonify(colormaps())


@flask_api.route('/legend', methods=['GET'])
@convert_exceptions
def get_legend() -> str:
    """Send back a JSON list of pixel value, color tuples"""
    from terracotta.handlers.legend import legend

    stretch_range = json.loads(request.args.get('stretch_range', 'null'))
    if not stretch_range:
        raise exceptions.InvalidArgumentsError('stretch_range argument must be given')

    colormap = request.args.get('colormap')
    num_values = int(request.args.get('num_values', 100))

    return jsonify(legend(stretch_range=stretch_range, colormap=colormap, num_values=num_values))


@flask_api.route('/', methods=['GET'])
def get_map() -> Any:
    if current_app.config.get('ALLOW_PREVIEW'):
        return render_template('map.html')
    abort(404)


def create_app(debug: bool = False, profile: bool = False) -> Flask:
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.register_blueprint(flask_api, url_prefix='')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.config['PROFILE'] = True
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    return new_app


def run_app(*args: Any, allow_all_ips: bool = False,
            port: int = 5000, preview: bool = False, **kwargs: Any) -> None:
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    app.config['ALLOW_PREVIEW'] = preview
    host = '0.0.0.0' if allow_all_ips else 'localhost'
    if preview and 'WERKZEUG_RUN_MAIN' not in os.environ:
        import threading
        import webbrowser

        def open_browser() -> None:
            webbrowser.open(f'http://127.0.0.1:{port}/')

        threading.Timer(2, open_browser).start()

    if os.environ.get('TC_TESTING'):
        return

    app.run(host=host, port=port)
