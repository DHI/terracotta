from flask import jsonify

from terracotta.api.flask_api import convert_exceptions, metadata_api


@metadata_api.route('/colormaps', methods=['GET'])
@convert_exceptions
def get_colormaps() -> str:
    """Send back a JSON list of all registered colormaps"""
    from terracotta.handlers.colormaps import colormaps
    return jsonify(colormaps())
