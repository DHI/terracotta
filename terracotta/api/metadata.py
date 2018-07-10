from flask import jsonify

from terracotta.api.flask_api import convert_exceptions, metadata_api


@metadata_api.route('/metadata/<path:path>', methods=['GET'])
@convert_exceptions
def get_metadata(path: str) -> str:
    """Send back dataset metadata as json"""
    from terracotta.handlers.metadata import metadata
    keys = [key for key in path.split('/') if key]
    meta = metadata(keys)
    return jsonify(meta)
