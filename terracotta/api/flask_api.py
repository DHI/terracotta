from typing import Callable, Any
import os
import functools

from apispec import APISpec
import apispec.ext.flask
import apispec.ext.marshmallow

from flask import Flask, Blueprint, current_app, send_file, jsonify
from flask_cors import CORS

import marshmallow

from terracotta import exceptions, __version__


# define blueprints, will be populated by submodules
tile_api = Blueprint('tile_api', 'terracotta')
metadata_api = Blueprint('metadata_api', 'terracotta')
preview_api = Blueprint('preview_api', 'terracotta')
spec_api = Blueprint('spec_api', 'terracotta')

CORS(metadata_api)  # allow access to metadata from all sources

# create an APISpec
spec = APISpec(
    title='Terracotta',
    version=__version__,
    openapi_version='2.0',
    info=dict(
        description='A modern XYZ Tile Server in Python'
    ),
    plugins=[
        apispec.ext.flask.FlaskPlugin(),
        apispec.ext.marshmallow.MarshmallowPlugin()
    ],
)


def abort(status_code: int, message: str = '') -> Any:
    response = jsonify({'message': message})
    response.status_code = status_code
    return response


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

        except exceptions.DatasetNotFoundError as exc:
            # wrong path -> 404
            if current_app.debug:
                raise
            return abort(404, str(exc))

        except (exceptions.InvalidArgumentsError, exceptions.UnknownKeyError,
                marshmallow.ValidationError) as exc:
            # wrong query arguments -> 400
            if current_app.debug:
                raise
            return abort(400, str(exc))

    return inner


def create_app(debug: bool = False,
               profile: bool = False,
               preview: bool = False) -> Flask:
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug

    # import submodules to populate blueprints
    import terracotta.api.colormaps
    import terracotta.api.datasets
    import terracotta.api.keys
    import terracotta.api.legend
    import terracotta.api.metadata
    import terracotta.api.rgb
    import terracotta.api.singleband

    new_app.register_blueprint(tile_api, url_prefix='')
    new_app.register_blueprint(metadata_api, url_prefix='')

    # register routes on API spec
    with new_app.test_request_context():
        spec.add_path(view=terracotta.api.colormaps.get_colormaps)
        spec.add_path(view=terracotta.api.datasets.get_datasets)
        spec.add_path(view=terracotta.api.keys.get_keys)
        spec.add_path(view=terracotta.api.legend.get_legend)
        spec.add_path(view=terracotta.api.metadata.get_metadata)
        spec.add_path(view=terracotta.api.rgb.get_rgb)
        spec.add_path(view=terracotta.api.singleband.get_singleband)

    if preview:
        import terracotta.api.map
        new_app.register_blueprint(preview_api, url_prefix='')

    import terracotta.api.spec
    new_app.register_blueprint(spec_api, url_prefix='')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.config['PROFILE'] = True
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    return new_app


def run_app(*args: Any, allow_all_ips: bool = False, port: int = 5000, **kwargs: Any) -> None:
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
