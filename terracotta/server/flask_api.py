from typing import Callable, Any
import functools

from apispec import APISpec
import apispec.ext.flask
import apispec.ext.marshmallow

from flask import Flask, Blueprint, current_app, send_file, jsonify
from flask_cors import CORS

import marshmallow

from terracotta import exceptions, __version__


# define blueprints, will be populated by submodules
tile_api = Blueprint('tile_api', 'terracotta.server')
metadata_api = Blueprint('metadata_api', 'terracotta.server')
spec_api = Blueprint('spec_api', 'terracotta.server')

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
            return send_file(image.empty_image(settings.DEFAULT_TILE_SIZE), mimetype='image/png')

        except exceptions.DatasetNotFoundError as exc:
            # wrong path -> 404
            if current_app.debug:
                raise
            return abort(404, str(exc))

        except (exceptions.InvalidArgumentsError, exceptions.InvalidKeyError,
                marshmallow.ValidationError) as exc:
            # wrong query arguments -> 400
            if current_app.debug:
                raise
            return abort(400, str(exc))

    return inner


def create_app(debug: bool = False, profile: bool = False) -> Flask:
    """Returns a Flask app"""

    new_app = Flask('terracotta.server')
    new_app.debug = debug

    # suppress implicit sort of JSON responses
    new_app.config['JSON_SORT_KEYS'] = False

    # import submodules to populate blueprints
    import terracotta.server.datasets
    import terracotta.server.keys
    import terracotta.server.colormap
    import terracotta.server.metadata
    import terracotta.server.rgb
    import terracotta.server.singleband

    new_app.register_blueprint(tile_api, url_prefix='')
    new_app.register_blueprint(metadata_api, url_prefix='')

    # register routes on API spec
    with new_app.test_request_context():
        spec.add_path(view=terracotta.server.datasets.get_datasets)
        spec.add_path(view=terracotta.server.keys.get_keys)
        spec.add_path(view=terracotta.server.colormap.get_colormap)
        spec.add_path(view=terracotta.server.metadata.get_metadata)
        spec.add_path(view=terracotta.server.rgb.get_rgb)
        spec.add_path(view=terracotta.server.rgb.get_rgb_preview)
        spec.add_path(view=terracotta.server.singleband.get_singleband)
        spec.add_path(view=terracotta.server.singleband.get_singleband_preview)

    import terracotta.server.spec
    new_app.register_blueprint(spec_api, url_prefix='')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    return new_app
