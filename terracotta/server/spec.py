"""server/spec.py

Flask routes to serve API spec
"""

from typing import Any

from flask import jsonify, render_template

from terracotta.server.flask_api import SPEC_API, SPEC


@SPEC_API.route('/swagger.json', methods=['GET'])
def specification() -> str:
    return jsonify(SPEC.to_dict())


@SPEC_API.route('/apidoc', methods=['GET'])
def ui() -> Any:
    return render_template('apidoc.html')
