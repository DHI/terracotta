import os
import threading
import webbrowser

from flask import Flask

import terracotta
import terracotta.config as config
from terracotta.tile_api import tile_api


def create_app(raster_files=None, cfg_file=None, debug=False, profile=False):
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.register_blueprint(tile_api, url_prefix='/terracotta')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.config['PROFILE'] = True
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    if cfg_file is not None:
        options, datasets = config.parse_cfg(cfg_file)
    elif raster_files is not None:
        options = config.default_cfg()
        import re
        datasets = {os.path.basename(r): {'name': os.path.basename(r), 'timestepped': False,
                                          'path': os.path.dirname(r) or '.',
                                          'regex': re.compile(os.path.basename(r) + '$')} for r in raster_files}
    else:
        raise ValueError('Either raster files or config file must be given')

    terracotta.tile_api.init(datasets, options['max_cache_size'])

    return new_app


def run_app(*args, preview=False, **kwargs):
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    port = 5000
    if preview and 'WERKZEUG_RUN_MAIN' not in os.environ:
        threading.Timer(2, lambda: webbrowser.open('http://127.0.0.1:%d/terracotta/' % port)).start()
    app.run(port=port)


if __name__ == '__main__':
    run_app('./config.cfg')
