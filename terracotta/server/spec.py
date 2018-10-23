"""server/spec.py

Flask routes to serve API spec
"""

from typing import Any

from flask import jsonify, render_template

from terracotta.server.flask_api import spec_api, spec


@spec_api.route('/swagger.json', methods=['GET'])
def specification() -> str:
    return jsonify(spec.to_dict())


@spec_api.route('/apidoc', methods=['GET'])
def ui() -> Any:
    return render_template('apidoc.html')
