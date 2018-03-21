from flask import Flask

import terracotta
import terracotta.config as config
from terracotta.tile_api import tile_api


def create_app(cfg_file, debug=False, profile=False):
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.register_blueprint(tile_api, url_prefix='/terracotta')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.config['PROFILE'] = True
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    options, datasets = config.parse_cfg(cfg_file)
    terracotta.tile_api.init(datasets, options['max_cache_size'])

    return new_app


def run_app(*args, **kwargs):
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    app.run()


if __name__ == '__main__':
    run_app('./config.cfg')
