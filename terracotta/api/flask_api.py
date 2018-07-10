from typing import Callable, Any
import os
import functools

from flask import Flask, Blueprint, current_app, abort, send_file
from flask_cors import CORS

from terracotta import exceptions


# define blueprints, will be populated by submodules

tile_api = Blueprint('tile_api', 'terracotta')

metadata_api = Blueprint('metadata_api', 'terracotta')
CORS(metadata_api)  # allow access to metadata from all sources

preview_api = Blueprint('preview_api', 'terracotta')


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


def create_app(debug: bool = False, profile: bool = False, preview: bool = False) -> Flask:
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug

    new_app.register_blueprint(tile_api, url_prefix='')
    new_app.register_blueprint(metadata_api, url_prefix='')

    if preview:
        new_app.register_blueprint(preview_api, url_prefix='')

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

    host = '0.0.0.0' if allow_all_ips else 'localhost'
    if kwargs.get('preview') and 'WERKZEUG_RUN_MAIN' not in os.environ:
        import threading
        import webbrowser

        def open_browser() -> None:
            webbrowser.open(f'http://127.0.0.1:{port}/')

        threading.Timer(2, open_browser).start()

    if os.environ.get('TC_TESTING'):  # set during pytest runs
        return

    app.run(host=host, port=port)
