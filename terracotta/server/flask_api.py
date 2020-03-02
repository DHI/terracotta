from typing import Callable, Any
import functools
import copy

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from flask import Flask, Blueprint, current_app, send_file, jsonify
from flask_cors import CORS

import marshmallow

from terracotta import exceptions, __version__


# define blueprints, will be populated by submodules
TILE_API = Blueprint('tile_api', 'terracotta.server')
METADATA_API = Blueprint('metadata_api', 'terracotta.server')
SPEC_API = Blueprint('spec_api', 'terracotta.server')

# create an APISpec
SPEC = APISpec(
    title='Terracotta',
    version=__version__,
    openapi_version='2.0',
    info=dict(
        description='A modern XYZ Tile Server in Python'
    ),
    plugins=[
        FlaskPlugin(),
        MarshmallowPlugin()
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
    from terracotta import get_settings
    import terracotta.server.datasets
    import terracotta.server.keys
    import terracotta.server.colormap
    import terracotta.server.metadata
    import terracotta.server.rgb
    import terracotta.server.singleband
    import terracotta.server.compute

    new_app = Flask('terracotta.server')
    new_app.debug = debug

    # extensions might modify the global blueprints, so copy before use
    new_tile_api = copy.deepcopy(TILE_API)
    new_metadata_api = copy.deepcopy(METADATA_API)

    # suppress implicit sort of JSON responses
    new_app.config['JSON_SORT_KEYS'] = False

    # CORS
    settings = get_settings()
    CORS(new_tile_api, origins=settings.ALLOWED_ORIGINS_TILES)
    CORS(new_metadata_api, origins=settings.ALLOWED_ORIGINS_METADATA)

    new_app.register_blueprint(new_tile_api, url_prefix='')
    new_app.register_blueprint(new_metadata_api, url_prefix='')

    # register routes on API spec
    with new_app.test_request_context():
        SPEC.path(view=terracotta.server.datasets.get_datasets)
        SPEC.path(view=terracotta.server.keys.get_keys)
        SPEC.path(view=terracotta.server.colormap.get_colormap)
        SPEC.path(view=terracotta.server.metadata.get_metadata)
        SPEC.path(view=terracotta.server.rgb.get_rgb)
        SPEC.path(view=terracotta.server.rgb.get_rgb_preview)
        SPEC.path(view=terracotta.server.singleband.get_singleband)
        SPEC.path(view=terracotta.server.singleband.get_singleband_preview)
        SPEC.path(view=terracotta.server.compute.get_compute)
        SPEC.path(view=terracotta.server.compute.get_compute_preview)

    import terracotta.server.spec
    new_app.register_blueprint(SPEC_API, url_prefix='')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        # use setattr to work around mypy false-positive (python/mypy#2427)
        setattr(
            new_app,
            'wsgi_app',
            ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])
        )

    return new_app
