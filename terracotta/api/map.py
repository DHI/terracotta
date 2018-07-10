from typing import Any

from flask import render_template

from terracotta.api.flask_api import preview_api


@preview_api.route('/', methods=['GET'])
def get_map() -> Any:
    return render_template('map.html')
