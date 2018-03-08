from flask import Flask

import terracotta
import terracotta.config as config
import terracotta.tile as tile


def create_app(cfg_file, debug=False):
    """Returns a Flask app"""
    from terracotta.tile_api import tile_api
    global tilestore

    options, datasets = config.parse_cfg(cfg_file)
    terracotta.tile_api.init_tilestore(datasets, options)

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.register_blueprint(tile_api)

    return new_app


def run_app(*args, **kwargs):
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    app.run()
