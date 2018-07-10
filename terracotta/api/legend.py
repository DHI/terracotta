import json

from flask import jsonify, request

from terracotta import exceptions
from terracotta.api.flask_api import convert_exceptions, metadata_api


@metadata_api.route('/legend', methods=['GET'])
@convert_exceptions
def get_legend() -> str:
    """Send back a JSON list of pixel value, color tuples"""
    from terracotta.handlers.legend import legend

    stretch_range = json.loads(request.args.get('stretch_range', 'null'))
    if not stretch_range:
        raise exceptions.InvalidArgumentsError('stretch_range argument must be given')

    colormap = request.args.get('colormap')
    num_values = int(request.args.get('num_values', 100))

    return jsonify(legend(stretch_range=stretch_range, colormap=colormap, num_values=num_values))
