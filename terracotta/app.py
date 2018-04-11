from flask import Flask

import terracotta
import terracotta.config as config
from terracotta.tile_api import tile_api


def create_app(cfg_file, debug=False):
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.register_blueprint(tile_api, url_prefix='')

    terracotta.tile_api.init(cfg_file)

    return new_app


def run_app(*args, **kwargs):
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    app.run()


if __name__ == '__main__':
    run_app('./config.cfg')
