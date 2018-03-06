from flask import Flask


def create_app(debug=False):
    """Returns a Flask app"""

    new_app = Flask('terracotta')
    new_app.debug = debug

    return new_app


def run_app(debug=False):
    """Create an app and run it"""

    app = create_app(debug)
    app.run()
