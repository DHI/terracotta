import os
import threading
import webbrowser

from flask import Flask

import terracotta
from terracotta.flask_api import flask_api


def create_app(raster_files=None, cfg_file=None, debug=False, profile=False):
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug
    new_app.register_blueprint(flask_api, url_prefix='')

    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        new_app.config['PROFILE'] = True
        new_app.wsgi_app = ProfilerMiddleware(new_app.wsgi_app, restrictions=[30])

    if cfg_file is not None:
        terracotta.flask_api.init(cfg_file=cfg_file)
    elif raster_files is not None:
        options = terracotta.config.default_cfg()
        import re
        datasets = {os.path.basename(r): {'name': os.path.basename(r), 'timestepped': False,
                                          'categorical': False, 'file': r} for r in raster_files}
        terracotta.flask_api.init(datasets=datasets, cache_size=options['max_cache_size'])
    else:
        raise ValueError('Either raster files or config file must be given')

    return new_app


def run_app(*args, preview=False, **kwargs):
    """Create an app and run it.
    All args are passed to create_app."""

    app = create_app(*args, **kwargs)
    port = 5000
    if preview and 'WERKZEUG_RUN_MAIN' not in os.environ:
        threading.Timer(2, lambda: webbrowser.open('http://127.0.0.1:%d/' % port)).start()
    app.run(port=port)


if __name__ == '__main__':
    run_app('./config.cfg')
