"""server/wmts.py

Flask route to handle /wmts calls.
"""

from flask import jsonify, Response, request
from marshmallow import Schema, fields

from terracotta.server.flask_api import METADATA_API


@METADATA_API.route('/wmts', methods=['GET'])
def get_wmts_capabilities() -> Response:
    from terracotta.handlers.wmts import wmts
    return Response(wmts(request.url_root), mimetype='text/xml')
