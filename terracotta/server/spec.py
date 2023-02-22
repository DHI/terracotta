"""server/spec.py

Flask routes to serve API spec
"""

from flask import jsonify, render_template, Response

from terracotta.server.flask_api import SPEC_API, SPEC


@SPEC_API.route('/swagger.json', methods=['GET'])
def specification() -> Response:
    return jsonify(SPEC.to_dict())


@SPEC_API.route('/apidoc', methods=['GET'])
def ui() -> str:
    return render_template('apidoc.html')
