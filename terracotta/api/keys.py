from flask import jsonify

from terracotta.api.flask_api import convert_exceptions, metadata_api


@metadata_api.route('/keys', methods=['GET'])
@convert_exceptions
def get_keys() -> str:
    """Send back a JSON list of all key names"""
    from terracotta.handlers.keys import keys
    return jsonify(keys())
