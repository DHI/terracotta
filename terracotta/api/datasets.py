from flask import jsonify, request

from terracotta.api.flask_api import convert_exceptions, metadata_api


@metadata_api.route('/datasets', methods=['GET'])
@convert_exceptions
def get_datasets() -> str:
    """Send back all available key combinations"""
    from terracotta.handlers.datasets import datasets
    keys = dict(request.args.items()) or None
    available_datasets = datasets(keys)
    return jsonify(available_datasets)
