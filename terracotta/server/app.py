"""server/app.py

Instantiated version of the Flask API.
"""

from terracotta import get_settings, logs
from terracotta.server import create_app

settings = get_settings()

logs.set_logger(
    settings.LOGLEVEL,
    catch_warnings=True
)

app = create_app(
    debug=settings.DEBUG,
    profile=settings.FLASK_PROFILE
)
