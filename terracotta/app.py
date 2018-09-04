"""app.py

Instantiated version of the Flask API.
"""

from terracotta import get_settings
from terracotta.api import create_app

settings = get_settings()
app = create_app(
    debug=settings.DEBUG,
    flask_profile=settings.FLASK_PROFILE,
    xray_profile=settings.XRAY_PROFILE
)
