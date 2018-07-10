
# import all route handlers to force blueprint registration
import terracotta.api.colormaps  # noqa: F401
import terracotta.api.datasets  # noqa: F401
import terracotta.api.keys  # noqa: F401
import terracotta.api.legend  # noqa: F401
import terracotta.api.map  # noqa: F401
import terracotta.api.metadata  # noqa: F401
import terracotta.api.rgb  # noqa: F401
import terracotta.api.singleband  # noqa: F401

from terracotta.api.flask_api import create_app, run_app  # noqa: F401
